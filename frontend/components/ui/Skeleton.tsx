export function SkeletonCard({ className = "" }: { className?: string }) {
  return (
    <div className={`bg-white rounded-3xl card-shadow animate-pulse ${className}`}>
      <div className="p-4">
        <div className="h-3 bg-[#F3F4F6] rounded-full w-16 mb-3" />
        <div className="h-4 bg-[#F3F4F6] rounded-full w-3/4 mb-2" />
        <div className="h-3 bg-[#F3F4F6] rounded-full w-full mb-1" />
        <div className="h-3 bg-[#F3F4F6] rounded-full w-2/3" />
      </div>
    </div>
  );
}

export function SkeletonStat() {
  return (
    <div className="bg-white rounded-3xl card-shadow p-5 animate-pulse">
      <div className="flex justify-between mb-4">
        <div>
          <div className="h-3 bg-[#F3F4F6] rounded-full w-20 mb-2" />
          <div className="h-8 bg-[#F3F4F6] rounded-full w-16" />
        </div>
        <div className="flex gap-4">
          <div>
            <div className="h-3 bg-[#F3F4F6] rounded-full w-10 mb-2" />
            <div className="h-6 bg-[#F3F4F6] rounded-full w-14" />
          </div>
        </div>
      </div>
      <div className="h-3 bg-[#F3F4F6] rounded-full w-full" />
    </div>
  );
}
