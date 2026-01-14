import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // SSR 전용 설정 - 정적 생성 비활성화
  output: "standalone",
};

export default nextConfig;
