
import { useEffect, useState } from 'react';
import { ArrowLeft, User, Settings, Moon, Bell, BarChart2, LogOut } from 'lucide-react';
import Navigation from '@/components/Navigation';
import { useNavigate } from 'react-router-dom';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { CircleProgress } from '@/components/CircleProgress';
import { supabase } from '@/integrations/supabase/client';
import { Tables } from '@/integrations/supabase/types';
import { toast } from '@/hooks/use-toast';
import { useAuth } from "@/contexts/AuthContext";

const chartData = [
  { name: 'Sun', value: 35 },
  { name: 'Mon', value: 45 },
  { name: 'Tue', value: 30 },
  { name: 'Wed', value: 65 },
  { name: 'Thu', value: 40 },
  { name: 'Fri', value: 50 },
  { name: 'Sat', value: 25 },
];

const goals = [
  {
    id: 1,
    title: "Weight",
    current: 165,
    target: 155,
    unit: "lbs",
    progress: 50
  },
  {
    id: 2,
    title: "Daily Steps",
    current: 8500,
    target: 10000,
    unit: "steps",
    progress: 85
  },
  {
    id: 3,
    title: "Workouts Per Week",
    current: 3,
    target: 5,
    unit: "workouts",
    progress: 60
  }
];

const settings = [
  {
    id: 'darkMode',
    icon: <Moon className="h-5 w-5" />,
    title: "Dark Mode",
    hasSwitch: true
  },
  {
    id: 'notifications',
    icon: <Bell className="h-5 w-5" />,
    title: "Notifications",
    hasSwitch: true
  },
  {
    id: 'profile',
    icon: <User className="h-5 w-5" />,
    title: "Edit Profile",
    hasSwitch: false
  },
  {
    id: 'settings',
    icon: <Settings className="h-5 w-5" />,
    title: "App Settings",
    hasSwitch: false
  },
  {
    id: 'logout',
    icon: <LogOut className="h-5 w-5" />,
    title: "Logout",
    hasSwitch: false,
    isDanger: true
  }
];

const WeeklyChart = () => {
  const maxValue = Math.max(...chartData.map(item => item.value));
  
  return (
    <div className="p-4 flex flex-col h-44">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-medium text-fit-primary">Weekly Activity</h3>
        <span className="text-xs text-fit-muted">Last 7 days</span>
      </div>
      
      <div className="flex-1 flex items-end gap-1">
        {chartData.map((item, index) => (
          <div key={index} className="flex-1 flex flex-col items-center h-full justify-end">
            <div 
              className="w-full rounded-t-md bg-fit-accent/80"
              style={{ height: `${(item.value / maxValue) * 100}%` }}
            ></div>
            <span className="text-[10px] text-fit-muted mt-1">{item.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const GoalCard = ({ goal }: { goal: typeof goals[0] }) => {
  return (
    <div className="fit-card p-4 mb-3">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-medium text-fit-primary">{goal.title}</h3>
        <span className="text-xs font-medium text-fit-primary">
          {goal.current} / {goal.target} <span className="text-fit-muted">{goal.unit}</span>
        </span>
      </div>
      <div className="h-1.5 bg-fit-secondary/30 rounded-full overflow-hidden">
        <div 
          className="h-full bg-fit-accent rounded-full"
          style={{ width: `${goal.progress}%` }}
        ></div>
      </div>
    </div>
  );
};

const SettingItem = ({ setting }: { setting: typeof settings[0] }) => {
  const navigate = useNavigate();
  
  const handleClick = () => {
    if (setting.id === 'profile') {
      navigate('/register');
    }
  };
  
  return (
    <div 
      className={`flex justify-between items-center py-3 border-b border-border/30 last:border-0 ${setting.isDanger ? 'text-red-500' : 'text-fit-primary'}`}
      onClick={handleClick}
      style={{ cursor: setting.hasSwitch ? 'default' : 'pointer' }}
    >
      <div className="flex items-center">
        {setting.icon}
        <span className="ml-3 font-medium">{setting.title}</span>
      </div>
      {setting.hasSwitch ? (
        <Switch id={setting.id} />
      ) : (
        <ArrowLeft className="h-4 w-4 rotate-180" />
      )}
    </div>
  );
};

const Profile = () => {
  const navigate = useNavigate();
  const [userProfile, setUserProfile] = useState<Tables<'user_profiles'> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    async function fetchUserProfile() {
      if (!user) {
        setIsLoading(false);
        return;
      }
      
      try {
        const { data, error } = await supabase
          .from('user_profiles')
          .select('*')
          .eq('user_id', user.id)
          .maybeSingle();
          
        if (error) {
          console.error('Error fetching profile:', error);
          toast({
            title: "Failed to load profile",
            description: error.message,
            variant: "destructive"
          });
        } else if (data) {
          setUserProfile(data);
          console.log('User profile loaded:', data);
        }
      } catch (err) {
        console.error('Unexpected error:', err);
      } finally {
        setIsLoading(false);
      }
    }

    fetchUserProfile();
  }, [user]);
  
  const updatedGoals = [...goals];
  if (userProfile) {
    const weightGoal = updatedGoals.find(g => g.title === "Weight");
    if (weightGoal) {
      weightGoal.current = userProfile.weight;
      weightGoal.target = Math.round(userProfile.weight * 0.95);
      weightGoal.progress = Math.min(100, Math.round((weightGoal.target / weightGoal.current) * 100));
    }
  }

  return (
    <div className="min-h-screen bg-fit-background">
      <header className="px-6 pt-12 pb-4 flex items-center">
        <button 
          onClick={() => navigate(-1)}
          className="mr-4 h-10 w-10 rounded-full flex items-center justify-center bg-fit-card hover:bg-fit-secondary/10 transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-fit-primary" />
        </button>
        <h1 className="text-xl font-semibold text-fit-primary">Profile</h1>
      </header>

      <main className="pb-20 px-6">
        {isLoading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-fit-accent"></div>
          </div>
        ) : (
          <>
            <div className="fit-card p-6 mb-6 flex items-center animate-fade-in">
              <Avatar className="h-16 w-16 border-2 border-fit-secondary">
                <AvatarImage src="/placeholder.svg" alt={userProfile?.name || "User"} />
                <AvatarFallback className="bg-fit-secondary text-white">
                  {userProfile?.name ? userProfile.name.charAt(0).toUpperCase() : 'U'}
                </AvatarFallback>
              </Avatar>
              
              <div className="ml-4">
                <h2 className="font-semibold text-fit-primary text-xl">{userProfile?.name || "User"}</h2>
                <div className="flex items-center mt-1">
                  <Badge variant="outline" className="mr-2 bg-amber-500/10 text-amber-500 border-amber-500/20">
                    <Trophy className="h-3 w-3 mr-1" />
                    Premium
                  </Badge>
                  <span className="text-xs text-fit-muted">
                    {userProfile ? `${userProfile.age} years • ${userProfile.region}` : "Member since 2023"}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="fit-card mb-6 animate-slide-up" style={{ animationDelay: '100ms' }}>
              <WeeklyChart />
            </div>
            
            <div className="mb-6 animate-slide-up" style={{ animationDelay: '200ms' }}>
              <h2 className="text-sm font-medium text-fit-muted mb-3">Fitness Goals</h2>
              {updatedGoals.map(goal => (
                <GoalCard key={goal.id} goal={goal} />
              ))}
            </div>
            
            {userProfile && (
              <div className="fit-card p-4 mb-6 animate-slide-up" style={{ animationDelay: '250ms' }}>
                <h2 className="text-sm font-medium text-fit-primary mb-4">Personal Information</h2>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-fit-muted">Height</span>
                    <span className="text-fit-primary font-medium">{userProfile.height} cm</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-fit-muted">Weight</span>
                    <span className="text-fit-primary font-medium">{userProfile.weight} kg</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-fit-muted">Gender</span>
                    <span className="text-fit-primary font-medium capitalize">{userProfile.gender}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-fit-muted">Activity Level</span>
                    <span className="text-fit-primary font-medium capitalize">{userProfile.activity_level.replace('-', ' ')}</span>
                  </div>
                  {userProfile.dietary_preferences && (
                    <div className="flex justify-between">
                      <span className="text-fit-muted">Diet</span>
                      <span className="text-fit-primary font-medium">{userProfile.dietary_preferences}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
            
            <div className="fit-card p-4 mb-6 animate-slide-up" style={{ animationDelay: '300ms' }}>
              <h2 className="text-sm font-medium text-fit-primary mb-4">Settings</h2>
              <div>
                {settings.map(setting => (
                  <SettingItem key={setting.id} setting={setting} />
                ))}
              </div>
            </div>
          </>
        )}
      </main>

      <Navigation />
    </div>
  );
};

import { Trophy } from 'lucide-react';

export default Profile;
