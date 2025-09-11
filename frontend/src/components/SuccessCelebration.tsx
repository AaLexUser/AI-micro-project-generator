import { useEffect, useState } from 'react';
import { CheckCircle, Trophy, Star, Sparkles, PartyPopper } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

interface SuccessCelebrationProps {
  isVisible: boolean;
  onAnimationComplete?: () => void;
}

export function SuccessCelebration({ isVisible, onAnimationComplete }: SuccessCelebrationProps) {
  const [showConfetti, setShowConfetti] = useState(false);
  const [showMessage, setShowMessage] = useState(false);

  useEffect(() => {
    if (isVisible) {
      // Start confetti animation
      setShowConfetti(true);

      // Show message after a short delay
      setTimeout(() => setShowMessage(true), 300);

      // Call completion callback after animations
      setTimeout(() => {
        onAnimationComplete?.();
      }, 3000);
    } else {
      setShowConfetti(false);
      setShowMessage(false);
    }
  }, [isVisible, onAnimationComplete]);

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none">
      {/* Confetti Animation */}
      {showConfetti && (
        <div className="absolute inset-0 overflow-hidden">
          {[...Array(50)].map((_, i) => (
            <div
              key={i}
              className="absolute animate-confetti"
              style={{
                left: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 2}s`,
                animationDuration: `${2 + Math.random() * 2}s`,
              }}
            >
              <div
                className="w-2 h-2 rounded-full"
                style={{
                  backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'][
                    Math.floor(Math.random() * 5)
                  ],
                }}
              />
            </div>
          ))}
        </div>
      )}

      {/* Success Message */}
      {showMessage && (
        <Card className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-200 shadow-2xl animate-success-bounce">
          <CardContent className="p-8 text-center space-y-6">
            <div className="relative">
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto animate-success-pulse">
                <Trophy className="w-10 h-10 text-green-600" />
              </div>
              <div className="absolute -top-2 -right-2 animate-spin">
                <Sparkles className="w-6 h-6 text-yellow-500" />
              </div>
              <div className="absolute -bottom-1 -left-1 animate-bounce">
                <Star className="w-5 h-5 text-yellow-400" />
              </div>
            </div>

            <div className="space-y-3">
              <h2 className="text-3xl font-bold text-green-800 animate-success-slide-up">
                🎉 Congratulations! 🎉
              </h2>
              <p className="text-lg text-green-700 animate-success-slide-up" style={{ animationDelay: '0.2s' }}>
                Project Completed Successfully!
              </p>
              <p className="text-green-600 animate-success-slide-up" style={{ animationDelay: '0.4s' }}>
                Your solution passed all tests with flying colors!
              </p>
            </div>

            <div className="flex items-center justify-center gap-2 text-green-600 animate-success-slide-up" style={{ animationDelay: '0.6s' }}>
              <CheckCircle className="w-5 h-5" />
              <span className="font-medium">Exit Code: 0</span>
              <PartyPopper className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
