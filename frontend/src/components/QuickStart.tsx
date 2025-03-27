import { Play, BarChart, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useRef } from 'react';

const QuickStart = () => {
  const openWorkoutsInNewTab = () => {
    window.open('/workouts', '_blank'); // ✅ Opens Workouts in a new tab
  };

  const progressRef = useRef(null); // ✅ Reference for Weekly Progress section

  const scrollToProgress = () => {
    if (progressRef.current) {
      progressRef.current.scrollIntoView({ behavior: 'smooth' }); // ✅ Scrolls to Weekly Progress
    }
  };

  return (
    <section className="px-6 py-4 animate-slide-up" style={{ animationDelay: '200ms' }}>
      <div className="space-y-3">
        {/* Start Workout Button */}
        <div 
          className="fit-card p-4 flex justify-between items-center cursor-pointer"
          onClick={openWorkoutsInNewTab} // ✅ Opens Workouts in a new tab
        >
          <div className="flex gap-4 items-center">
            <div className="h-12 w-12 rounded-xl bg-[#4EAF83]/10 flex items-center justify-center">
              <Play className="h-5 w-5 text-[#4EAF83]" />
            </div>
            <div>
              <h3 className="font-medium text-fit-primary">Start Workout</h3>
              <p className="text-xs text-fit-muted">Continue your training</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" className="rounded-full h-8 w-8 bg-fit-card hover:bg-fit-secondary/10">
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        {/* Weekly Progress Button */}
        <div 
          className="fit-card p-4 flex justify-between items-center cursor-pointer"
          onClick={scrollToProgress} // ✅ Scrolls to Weekly Progress section
        >
          <div className="flex gap-4 items-center">
            <div className="h-12 w-12 rounded-xl bg-[#A0D2EB]/10 flex items-center justify-center">
              <BarChart className="h-5 w-5 text-[#A0D2EB]" />
            </div>
            <div>
              <h3 className="font-medium text-fit-primary">Weekly Progress</h3>
              <p className="text-xs text-fit-muted">View your stats</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" className="rounded-full h-8 w-8 bg-fit-card hover:bg-fit-secondary/10">
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Weekly Progress Section */}
      <div ref={progressRef} className="mt-10 p-4 bg-gray-100 rounded-lg text-center">
        <h3 className="text-lg font-semibold text-fit-primary">Weekly Progress</h3>
        <p className="text-sm text-fit-muted">Here’s how you’re doing this week! 📊</p>
      </div>
    </section>
  );
};

export default QuickStart;
