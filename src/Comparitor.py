import cv2
import ffmpeg
import numpy as np
from numba import cuda, njit
from psnr_hvsm import psnr_hvs_hvsm
from imageio import imread

@njit
def numba_ssim(img1: np.ndarray, img2: np.ndarray, K1=0.01, K2=0.03, window_size=11, L=255):
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    
    C1 = (K1 * L) ** 2
    C2 = (K2 * L) ** 2
    
    window = np.ones((window_size, window_size)) / window_size ** 2
    
    mu1 = cv2.filter2D(img1, -1, window)
    mu2 = cv2.filter2D(img2, -1, window)
    
    mu1_sq = mu1 * mu1
    mu2_sq = mu2 * mu2
    mu1_mu2 = mu1 * mu2
    
    sigma1_sq = cv2.filter2D(img1 * img1, -1, window) - mu1_sq
    sigma2_sq = cv2.filter2D(img2 * img2, -1, window) - mu2_sq
    sigma12 = cv2.filter2D(img1 * img2, -1, window) - mu1_mu2
    
    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    
    return ssim_map.mean()

@cuda.jit(device=True)
def _ssim_cuda(img1: float64[:, :], img2: float64[:, :], x: int32, y: int32, window_size: int32, C1: float64, C2: float64) -> float64:
    mu1 = 0.0
    mu2 = 0.0
    for i in range(window_size):
        for j in range(window_size):
            mu1 += img1[x+i, y+j]
            mu2 += img2[x+i, y+j]
    
    mu1 /= window_size * window_size
    mu2 /= window_size * window_size
    
    mu1_sq = mu1 * mu1
    mu2_sq = mu2 * mu2
    mu1_mu2 = mu1 * mu2
    
    sigma1_sq = 0.0
    sigma2_sq = 0.0
    sigma12 = 0.0
    
    for i in range(window_size):
        for j in range(window_size):
            img1_val = img1[x+i, y+j]
            img2_val = img2[x+i, y+j]
            
            sigma1_sq += img1_val * img1_val
            sigma2_sq += img2_val * img2_val
            sigma12 += img1_val * img2_val
    
    sigma1_sq = (sigma1_sq / (window_size * window_size)) - mu1_sq
    sigma2_sq = (sigma2_sq / (window_size * window_size)) - mu2_sq
    sigma12 = (sigma12 / (window_size * window_size)) - mu1_mu2
    
    ssim = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    
    return ssim

@cuda.jit
def ssim_cuda_kernel(img1: np.ndarray, img2: np.ndarray, ssim_map: np.ndarray, window_size: int, C1: float, C2: float):
    x, y = cuda.grid(2)
    
    if x < img1.shape[0] - window_size and y < img1.shape[1] - window_size:
        ssim_map[x, y] = _ssim_cuda(img1, img2, x, y, window_size, C1, C2)

def ssim_cuda(img1: np.ndarray, img2: np.ndarray, K1: float=0.01, K2: float=0.03, window_size: int=11, L: int=255) -> float:
    img1 = img1.astype(np.float32)
    img2 = img2.astype(np.float32)
    
    C1 = (K1 * L) ** 2
    C2 = (K2 * L) ** 2
    
    ssim_map = np.zeros((img1.shape[0] - window_size, img1.shape[1] - window_size), dtype=np.float32)
    
    threadsperblock = (16, 16)
    blockspergrid_x = int(np.ceil(img1.shape[0] / threadsperblock[0]))
    blockspergrid_y = int(np.ceil(img1.shape[1] / threadsperblock[1]))
    blockspergrid = (blockspergrid_x, blockspergrid_y)
    
    ssim_cuda_kernel[blockspergrid, threadsperblock](img1, img2, ssim_map, window_size, C1, C2)
    
    return ssim_map.mean()

def compare_videos(video1_path, video2_path, accelerator='cpu'):
    # Read video streams
    video1 = cv2.VideoCapture(video1_path)
    video2 = cv2.VideoCapture(video2_path)

    # Check if both videos are opened
    if not video1.isOpened() or not video2.isOpened():
        raise ValueError("Could not open one or both video files.")

    # Calculate the metrics
    psnr_values = []
    ssim_values = []
    ms_ssim_values = []
    vmaf_values = []
    psnr_hvs_values = []

    use_opencl = accelerator.lower() == 'opencl'
    use_cuda = accelerator.lower() == 'cuda'

    while True:
        ret1, frame1 = video1.read()
        ret2, frame2 = video2.read()

        # Break the loop if either video has ended
        if not ret1 or not ret2:
            break

        if use_opencl:
            frame1 = cv2.UMat(frame1)
            frame2 = cv2.UMat(frame2)

        # Calculate PSNR
        psnr = cv2.PSNR(frame1, frame2)
        psnr_values.append(psnr)

        # Calculate SSIM
        if use_cuda:
            calculate_ssim_cuda(frame1, frame2, ssim_values)
        else:
            ssim = cv2.compare_ssim(frame1, frame2, multichannel=True)
            ssim_values.append(ssim)

        # Calculate MS-SSIM
        ms_ssim = cv2.MSSSIM(frame1, frame2)
        ms_ssim_values.append(ms_ssim)

        # Calculate VMAF
        vmaf = ffmpeg.filter([ffmpeg.input(video1_path), ffmpeg.input(video2_path)], 'libvmaf')
        vmaf_values.append(vmaf)

        # Calculate PSNR-HVS
        frame1_normalized = frame1.astype(float) / 255
        frame2_normalized = frame2.astype(float) / 255
        psnr_hvs, _ = psnr_hvs_hvsm(frame1_normalized, frame2_normalized)
        psnr_hvs_values.append(psnr_hvs)

    # Calculate average values
    avg_psnr = np.mean(psnr_values)
    avg_ssim = np.mean(ssim_values)
    avg_ms_ssim = np.mean(ms_ssim_values)
    avg_vmaf = np.mean(vmaf_values)
    avg_psnr_hvs = np.mean(psnr_hvs_values)

    return avg_psnr, avg_ssim, avg_ms_ssim, avg_vmaf, avg_psnr_hvs

if __name__ == '__main__':
    video1_path = 'video1.mp4'
    video2_path = 'video2.mp4'
    accelerator = 'opencl'  # or 'cuda' or 'cpu'

    psnr, ssim, ms_ssim, vmaf, psnr_hvs = compare_videos(video1_path, video2_path, accelerator)

    print(f"PSNR: {psnr:.2f}")
    print(f"SSIM: {ssim:.2f}")
    print(f"MS-SSIM: {ms_ssim:.2f}")
    print(f"VMAF: {vmaf:.2f}")
    print(f"PSNR-HVS: {psnr_hvs:.2f}")
