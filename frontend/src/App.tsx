import React, { useState, useEffect, useRef } from 'react';
import { 
  Trophy, 
  Bot, 
  Moon, 
  Sun, 
  Play, 
  RefreshCw,
  Search,
  ChevronRight,
  AlertCircle,
  Settings,
  LogOut,
  Clock
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

interface RaceState {
  id: string;
  start_page: string;
  target_page: string;
  status: 'playing' | 'waiting' | 'finished';
  winner?: 'human' | 'bot';
}

function App() {
  const [race, setRace] = useState<RaceState | null>(null);
  const [botPath, setBotPath] = useState<string[]>([]);
  const [winner, setWinner] = useState<string | null>(null);
  const [botDelay, setBotDelay] = useState<number>(5);
  const [startTime, setStartTime] = useState<number | null>(null);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [botThinking, setBotThinking] = useState(false);
  const [isDark, setIsDark] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const logEndRef = useRef<HTMLDivElement>(null);

  // Theme handling
  useEffect(() => {
    const root = window.document.documentElement;
    if (isDark) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [isDark]);

  useEffect(() => {
    if (race?.status === 'playing' && !winner) {
      const interval = setInterval(() => {
        setCurrentTime(Date.now() - (startTime || Date.now()));
      }, 100);
      return () => clearInterval(interval);
    }
  }, [race?.status, winner, startTime]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [botPath]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startNewRace = async () => {
    setLoading(true);
    setError(null);
    setRace(null);
    setBotPath([]);
    setWinner(null);
    setStartTime(null);
    setCurrentTime(0);
    setBotThinking(false);

    try {
      const response = await fetch('http://localhost:8000/api/race/new', { method: 'POST' });
      if (!response.ok) throw new Error('Failed to create race');
      const data = await response.json();
      setRace({ ...data, status: 'waiting' });
      setBotPath([data.start_page]);
      setWinner(null);
      setStartTime(null);
      setCurrentTime(0);

      // Setup WebSocket
      if (socketRef.current) socketRef.current.close();
      const ws = new WebSocket(`ws://localhost:8000/api/ws/${data.id}`);
      
      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === 'GAME_START') {
          setRace(prev => prev ? { ...prev, status: 'playing' } : null);
          setStartTime(Date.now());
        } else if (msg.type === 'BOT_THINKING') {
          setBotThinking(true);
        } else if (msg.type === 'BOT_MOVED') {
          setBotThinking(false);
          setBotPath(msg.path);
        } else if (msg.type === 'BOT_RESTARTED') {
          setBotThinking(false);
          setBotPath([data.start_page]);
        } else if (msg.type === 'SETTINGS_UPDATED') {
          setBotDelay(msg.botDelay);
        } else if (msg.type === 'RACE_OVER') {
          setBotThinking(false);
          setWinner(msg.winner);
          if (msg.winner === 'bot' && msg.path) {
            setBotPath(msg.path);
          }
          setRace(prev => prev ? { ...prev, status: 'finished' } : null);
        }
      };
      ws.onerror = () => setError('WebSocket connection error');
      ws.onclose = () => {
        if (race?.status === 'playing' && !winner) {
          setError('Disconnected from game server');
        }
      };
      socketRef.current = ws;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleStartGame = () => {
    if (socketRef.current && race?.status === 'waiting') {
      socketRef.current.send(JSON.stringify({ type: 'START_RACE', botDelay }));
    }
  };

  const handleUpdateDelay = (newDelay: number) => {
    setBotDelay(newDelay);
    if (socketRef.current && race?.status === 'playing') {
      socketRef.current.send(JSON.stringify({ type: 'UPDATE_SETTINGS', botDelay: newDelay }));
    }
  };

  const resetGame = () => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    setRace(null);
    setBotPath([]);
    setWinner(null);
    setStartTime(null);
    setCurrentTime(0);
    setBotThinking(false);
    setError(null);
  };

  const formatTime = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const tenths = Math.floor((ms % 1000) / 100);
    return `${minutes}:${(seconds % 60).toString().padStart(2, '0')}.${tenths}`;
  };

  return (
    <TooltipProvider>
      <div className="h-screen bg-background text-foreground font-sans transition-colors duration-300 flex flex-col overflow-hidden">
        <header className="shrink-0 w-full border-b bg-background">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Trophy className="h-6 w-6 text-primary" />
              <span className="text-xl font-bold tracking-tight text-foreground">WikiRacer</span>
            </div>
            <div className="flex items-center gap-4">
              {race && (
                <Badge variant="outline" className="px-3 py-1 font-mono text-xs">
                  {formatTime(currentTime)}
                </Badge>
              )}
              
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-9 w-9">
                    <Settings className="h-5 w-5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>Game Settings</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <div className="px-2 py-2">
                    <div className="flex flex-col gap-2">
                      <Label htmlFor="menu-bot-delay" className="text-xs font-medium flex items-center gap-2">
                        <Clock className="h-3 w-3" /> Bot Delay: {botDelay}s
                      </Label>
                      <Input 
                        id="menu-bot-delay"
                        type="range" 
                        min="1" 
                        max="30"
                        step="1"
                        value={botDelay} 
                        onChange={(e) => handleUpdateDelay(Number(e.target.value))} 
                        className="h-6"
                      />
                    </div>
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={resetGame} className="text-destructive focus:text-destructive cursor-pointer">
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>Quit Race / Reset</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-9 w-9"
                    onClick={() => setIsDark(!isDark)}
                  >
                    {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Toggle theme</p>
                </TooltipContent>
              </Tooltip>
            </div>
          </div>
        </header>

        <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-4 flex flex-col gap-4 overflow-hidden">
          {error && (
            <Alert variant="destructive" className="animate-in fade-in slide-in-from-top-4 duration-300">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {!race ? (
            <div className="flex-1 flex flex-col items-center justify-center max-w-2xl mx-auto w-full gap-8 py-12">
              <div className="text-center flex flex-col gap-2">
                <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
                  The Wikipedia Race
                </h1>
                <p className="text-lg text-muted-foreground leading-relaxed">
                  Race from one random article to another. Beat the AI to the finish line!
                </p>
              </div>

              <Card className="w-full max-w-md shadow-none">
                <CardHeader>
                  <CardTitle className="text-base font-semibold">Game Settings</CardTitle>
                  <CardDescription>Configure your race parameters before starting.</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col gap-6">
                  <div className="flex flex-col gap-2">
                    <Label htmlFor="bot-delay" className="text-sm font-medium">Bot Move Delay (seconds)</Label>
                    <div className="flex items-center gap-4">
                      <Input 
                        id="bot-delay"
                        type="number" 
                        min="1" 
                        max="60"
                        className="max-w-[120px]"
                        value={botDelay} 
                        onChange={(e) => setBotDelay(Number(e.target.value))} 
                      />
                      <p className="text-sm text-muted-foreground leading-snug">
                        Lower values make the bot faster and more difficult.
                      </p>
                    </div>
                  </div>
                  <Button 
                    size="default"
                    className="w-full font-medium" 
                    onClick={startNewRace} 
                    disabled={loading}
                  >
                    {loading ? (
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Play className="mr-2 h-4 w-4" />
                    )}
                    {loading ? 'Generating Path...' : 'Generate Random Race'}
                  </Button>
                </CardContent>
              </Card>
            </div>
          ) : (
            <div className="flex-1 grid grid-cols-1 lg:grid-cols-10 gap-6 overflow-hidden min-h-0">
              <Card className="lg:col-span-7 flex flex-col overflow-hidden shadow-none border-border h-full">
                {race.status === 'waiting' ? (
                  <div className="flex-1 flex flex-col items-center justify-center p-12 text-center gap-8">
                    <div className="flex flex-col gap-4">
                      <div><Badge variant="secondary" className="text-sm px-4 py-1">New Race Ready</Badge></div>
                      <h2 className="text-3xl font-semibold tracking-tight text-foreground">Can you win?</h2>
                    </div>
                    
                    <div className="flex flex-col sm:flex-row items-center gap-4 sm:gap-12 w-full max-w-lg">
                      <div className="flex-1 flex flex-col gap-2">
                        <Label className="text-sm font-medium text-muted-foreground uppercase tracking-wider">START</Label>
                        <p className="text-xl font-semibold text-foreground leading-tight">{race.start_page}</p>
                      </div>
                      <ChevronRight className="h-8 w-8 text-muted-foreground/30 hidden sm:block" />
                      <div className="flex-1 flex flex-col gap-2">
                        <Label className="text-sm font-medium text-muted-foreground uppercase tracking-wider">TARGET</Label>
                        <p className="text-xl font-semibold text-primary leading-tight">{race.target_page}</p>
                      </div>
                    </div>

                    <Button size="default" className="font-semibold h-11 px-8" onClick={handleStartGame}>
                      START RACE!
                    </Button>
                  </div>
                ) : (
                  <div className="flex-1 relative bg-white">
                    <iframe 
                      key={race.id}
                      src={`http://localhost:8000/api/proxy/${race.id}/${race.start_page.replace(/ /g, '_')}`}
                      title="Wikipedia"
                      className="absolute inset-0 w-full h-full border-none"
                    />
                  </div>
                )}
              </Card>
              
              <div className="lg:col-span-3 flex flex-col gap-6 overflow-hidden">
                <Card className="shadow-none">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Target Article</CardTitle>
                      <Search className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="p-4 bg-muted/50 border border-border rounded-lg text-center">
                      <p className="text-xl font-bold text-primary tracking-tight">{race.target_page}</p>
                    </div>
                  </CardContent>
                </Card>

                <Card className="flex-1 flex flex-col overflow-hidden shadow-none">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base font-semibold text-foreground">Bot Activity</CardTitle>
                      <Badge 
                        variant={botThinking ? "secondary" : "default"}
                        className={cn(
                          "transition-all duration-300",
                          botThinking && "animate-pulse"
                        )}
                      >
                        {botThinking ? (
                          <span className="flex items-center gap-1"><RefreshCw className="h-3 w-3 animate-spin" /> Thinking...</span>
                        ) : (
                          <span className="flex items-center gap-1"><Play className="h-3 w-3" /> Moving...</span>
                        )}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="flex-1 flex flex-col gap-4 overflow-hidden pt-0">
                    <Separator />
                    <ScrollArea className="flex-1 pr-4">
                      <div className="flex flex-col gap-2 pt-4">
                        {botPath.length === 0 ? (
                          <div className="flex flex-col items-center justify-center py-12 text-center">
                            <Bot className="h-8 w-8 text-muted-foreground mb-3 opacity-20" />
                            <p className="text-sm font-medium text-foreground mb-1">Waiting for race start</p>
                            <p className="text-xs text-muted-foreground">
                              The bot will begin its journey once you click GO!
                            </p>
                          </div>
                        ) : (
                          botPath.map((page, i) => (
                            <div key={i} className="flex items-start gap-3 group animate-in fade-in slide-in-from-left-2 duration-300">
                              <div className="flex flex-col items-center gap-1 mt-1">
                                <div className={cn(
                                  "h-5 w-5 rounded-full flex items-center justify-center text-[10px] font-bold",
                                  i === botPath.length - 1 ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                                )}>
                                  {i + 1}
                                </div>
                                {i < botPath.length - 1 && <div className="w-[1px] h-4 bg-border" />}
                              </div>
                              <p className={cn(
                                "text-sm leading-tight pt-0.5",
                                i === botPath.length - 1 ? "font-bold text-foreground" : "text-muted-foreground"
                              )}>
                                {page}
                              </p>
                            </div>
                          ))
                        )}
                        <div ref={logEndRef} />
                      </div>
                    </ScrollArea>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {winner && (
            <div className="fixed inset-0 z-[100] flex items-center justify-center bg-background/80 p-4 animate-in fade-in duration-300">
              <Card className="w-full max-w-md border border-border shadow-lg animate-in zoom-in-95 duration-300 overflow-hidden flex flex-col">
                <CardHeader className="text-center flex flex-col gap-2 shrink-0">
                  <div className="mx-auto w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-2">
                    <Trophy className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle className="text-2xl font-semibold tracking-tight text-foreground">
                    {winner === 'human' ? 'VICTORY!' : 'DEFEAT!'}
                  </CardTitle>
                  <CardDescription className="text-sm text-muted-foreground leading-relaxed">
                    {winner === 'human' ? "You've outsmarted the machine." : "The AI reached the destination first."}
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col gap-6 overflow-hidden">
                  <div className="flex justify-between items-center p-4 bg-muted rounded-lg shrink-0">
                    <div className="text-sm font-medium text-muted-foreground">Final Time</div>
                    <div className="text-2xl font-bold text-foreground font-mono tabular-nums">{formatTime(currentTime)}</div>
                  </div>

                  {winner === 'bot' && (
                    <div className="flex-1 flex flex-col gap-3 min-h-0 overflow-hidden">
                      <div className="flex items-center gap-2 px-1">
                        <Bot className="h-4 w-4 text-primary" />
                        <span className="text-sm font-medium text-foreground">AI's Winning Path</span>
                        <Badge variant="outline" className="ml-auto font-mono text-[10px]">{botPath.length} steps</Badge>
                      </div>
                      <ScrollArea className="flex-1 rounded-md border bg-muted/30 p-4">
                        <div className="flex flex-col gap-3">
                          {botPath.map((page, i) => (
                            <div key={i} className="flex items-start gap-3 group">
                              <span className="text-[10px] font-mono text-muted-foreground mt-1 w-4 shrink-0">{i + 1}</span>
                              <span className="text-xs leading-tight font-medium group-last:text-primary group-last:font-bold">
                                {page}
                              </span>
                            </div>
                          ))}
                        </div>
                      </ScrollArea>
                    </div>
                  )}

                  <Button size="default" className="w-full font-bold h-11 shrink-0" onClick={startNewRace}>
                    <RefreshCw className="mr-2 h-4 w-4" /> Start New Race
                  </Button>
                </CardContent>
              </Card>
            </div>
          )}
        </main>
      </div>
    </TooltipProvider>
  );
}

export default App;
