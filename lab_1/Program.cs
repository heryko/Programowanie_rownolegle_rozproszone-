﻿using System;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;

namespace miners
{
    class Program
    {
        const int DepositSize = 2000;
        const int VehicleCapacity = 200;
        const int MiningTime = 10;
        const int UnloadingTime = 10;
        const int TravelTime = 10000;
        const int RefreshTime = 100;

        static int remainingCoal;
        static int warehouseCoal;
        static string[] statuses;
        static SemaphoreSlim depositSemaphore;
        static SemaphoreSlim warehouseSemaphore;

        static object lockObject = new object();
        static object consoleLock = new object();
        static volatile bool finished = false;

        static void Main(string[] args)
        {
            Console.Clear();
            Console.CursorVisible = false;

            int maxMiners = 6;
            double[] executionTimes = new double[maxMiners + 1];

            // 1 do 6
            for (int p = 1; p <= maxMiners; p++)
            {
                executionTimes[p] = RunSimulation(p);
            }

            Console.Clear();
            Console.SetCursorPosition(0, 0);
            Console.WriteLine("WYNIKI POMIARÓW");
            double t1 = executionTimes[1];

            for (int p = 1; p <= maxMiners; p++)
            {
                double speedup = t1 / executionTimes[p];
                double efficiency = speedup / p;

                Console.WriteLine($"liczba górników: {p}, czas: {executionTimes[p]:F2} s " +
                                  $"przyśpieszenie: {speedup:F2} efektywność: {efficiency:F2}");
            }

            Console.CursorVisible = true;
            Console.WriteLine("\nNaciśnij dowolny klawisz, aby zakończyć...");
            Console.ReadKey();
        }

        static double RunSimulation(int minerCount)
        {
            Console.Clear();
            remainingCoal = DepositSize;
            warehouseCoal = 0;
            statuses = new string[minerCount];
            depositSemaphore = new SemaphoreSlim(2, 2);
            warehouseSemaphore = new SemaphoreSlim(1, 1);
            finished = false;

            for (int i = 0; i < minerCount; i++)
                statuses[i] = "Czeka na start...";

            Stopwatch time = Stopwatch.StartNew();
            Thread display = new Thread(() => DisplayStatus(minerCount));
            display.Start();

            Task[] miners = new Task[minerCount];
            for (int i = 0; i < miners.Length; i++)
            {
                int id = i + 1;
                miners[i] = Task.Run(() => MinerWork(id));
            }
            Task.WaitAll(miners);
            time.Stop();

            finished = true;
            display.Join();

            return time.Elapsed.TotalSeconds;
        }

        static void DisplayStatus(int minerCount)
        {
            while (!finished)
            {
                Draw(minerCount);
                Thread.Sleep(RefreshTime);
            }
            Draw(minerCount);
        }

        static void Draw(int minerCount)
        {
            int deposit;
            int warehouse;
            string[] statusCopy = new string[minerCount];
            lock (lockObject)
            {
                deposit = remainingCoal;
                warehouse = warehouseCoal;
                Array.Copy(statuses, statusCopy, minerCount);
            }

            lock (consoleLock)
            {
                Console.SetCursorPosition(0, 0);
                Console.WriteLine($"--- Symulacja dla {minerCount} górników ---".PadRight(50));
                Console.WriteLine($"Stan złoża: {deposit} jednostek węgla".PadRight(50));
                Console.WriteLine($"Stan magazynu: {warehouse} jednostek węgla".PadRight(50));
                Console.WriteLine("".PadRight(50));
                for (int i = 0; i < minerCount; i++)
                {
                    Console.WriteLine($"Górnik {i + 1}: {statusCopy[i]}".PadRight(50));
                }
            }
        }

        static void SetStatus(int id, string text)
        {
            lock (lockObject)
            {
                statuses[id - 1] = text;
            }
        }

        static void MinerWork(int id)
        {
            while (true)
            {
                lock (lockObject)
                {
                    if (remainingCoal <= 0)
                    {
                        SetStatus(id, "zakończył pracę.");
                        return;
                    }
                }

                int loadedCoal = 0;
                SetStatus(id, "Czeka na wejście do złoża......");
                depositSemaphore.Wait();
                SetStatus(id, "Wydobywa węgiel......");
                while (loadedCoal < VehicleCapacity)
                {
                    bool mined = false;
                    lock (lockObject)
                    {
                        if (remainingCoal > 0)
                        {
                            remainingCoal--;
                            mined = true;
                        }
                    }
                    if (!mined) break;

                    Thread.Sleep(MiningTime);
                    loadedCoal++;
                }
                depositSemaphore.Release();

                if (loadedCoal == 0)
                {
                    SetStatus(id, "zakończył pracę.");
                    return;
                }

                SetStatus(id, "Transportuje do magazynu...");
                Thread.Sleep(TravelTime);

                SetStatus(id, "Czeka na rozładunek...");
                warehouseSemaphore.Wait();
                SetStatus(id, "Rozładowuje węgiel...");
                for (int i = 0; i < loadedCoal; i++)
                {
                    Thread.Sleep(UnloadingTime);
                    lock (lockObject)
                    {
                        warehouseCoal++;
                    }
                }
                warehouseSemaphore.Release();

                SetStatus(id, "Wraca do złoża...");
                Thread.Sleep(TravelTime);
            }
        }
    }
}