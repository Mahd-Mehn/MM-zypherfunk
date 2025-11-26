"use client";

import { useEffect, useState } from 'react';
import { useObscuraStream } from '@/hooks/useObscuraStream';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Activity, ShieldCheck, ArrowUpRight, ArrowDownRight } from 'lucide-react';

export function LiveActivityFeed() {
  // Mock User ID for demo
  const userId = "demo-user-123";
  const { isConnected, lastMessage } = useObscuraStream(userId);
  const [activities, setActivities] = useState<any[]>([]);

  useEffect(() => {
    if (lastMessage) {
      setActivities((prev) => [lastMessage, ...prev].slice(0, 50)); // Keep last 50
    }
  }, [lastMessage]);

  return (
    <Card className="w-full h-[400px] flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">
          Live Network Activity
        </CardTitle>
        <Badge variant={isConnected ? "default" : "destructive"}>
          {isConnected ? "Live" : "Connecting..."}
        </Badge>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden">
        <ScrollArea className="h-full pr-4">
          <div className="space-y-4">
            {activities.length === 0 && (
              <div className="text-center text-muted-foreground text-sm py-8">
                Waiting for network events...
              </div>
            )}
            
            {activities.map((activity, i) => (
              <div key={i} className="flex items-start space-x-4 border-b pb-4 last:border-0">
                <div className={`p-2 rounded-full ${
                  activity.type === 'trade_update' ? 'bg-blue-100 text-blue-600' : 'bg-green-100 text-green-600'
                }`}>
                  {activity.type === 'trade_update' ? <Activity size={16} /> : <ShieldCheck size={16} />}
                </div>
                <div className="space-y-1 flex-1">
                  <p className="text-sm font-medium leading-none">
                    {activity.type === 'trade_update' ? 'Copy Trade Executed' : 'ZK Proof Verified'}
                  </p>
                  <div className="text-xs text-muted-foreground">
                    {activity.type === 'trade_update' ? (
                      <span className="flex items-center gap-1">
                        {activity.data.side.toUpperCase()} {activity.data.amount} {activity.data.symbol} on {activity.data.exchange}
                        {activity.data.side === 'buy' ? <ArrowUpRight size={12} className="text-green-500"/> : <ArrowDownRight size={12} className="text-red-500"/>}
                      </span>
                    ) : (
                      <span>
                        Trade {activity.data.trade_id.slice(0, 8)}... verified with ROI {activity.data.roi_percentage?.toFixed(2)}%
                      </span>
                    )}
                  </div>
                  <p className="text-[10px] text-muted-foreground">
                    {new Date(activity.timestamp * 1000).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
