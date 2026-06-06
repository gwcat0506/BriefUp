/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // 배포 시 이미지 최적화
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;
