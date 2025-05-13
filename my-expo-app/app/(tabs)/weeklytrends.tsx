import React, { useEffect, useState } from 'react';
import { View, Text, Dimensions, ScrollView } from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { getWeeklyTrends } from '../../utils/api';
import { SafeAreaView } from 'react-native-safe-area-context'

const screenWidth = Dimensions.get('window').width;

type TrendItem = {
  WeekLabel: string;
  Deposits: number;
  Withdrawals: number;
};

const WeeklyTrends = () => {
  const [trends, setTrends] = useState<TrendItem[]>([]);

  useEffect(() => {
    const fetchTrends = async () => {
      try {
        const data = await getWeeklyTrends();
        setTrends(data);
      } catch (error) {
        console.error('Error fetching weekly trends:', error);
      }
    };
    fetchTrends();
  }, []);

  if (!trends.length) return <Text style={{ padding: 16 }}>Loading trends...</Text>;

  const labels = trends.map(item => {
    const parts = item.WeekLabel.split(' - ');
    return parts[1] || item.WeekLabel; // e.g., "Week 1"
  });
    const deposits = trends.map(item => item.Deposits || 0);
  const withdrawals = trends.map(item => item.Withdrawals || 0);

  const chartData = {
    labels,
    datasets: [
      {
        data: deposits,
        color: (opacity = 1) => `rgba(0, 200, 0, ${opacity})`,
        strokeWidth: 2,
      },
      {
        data: withdrawals,
        color: (opacity = 1) => `rgba(255, 0, 0, ${opacity})`,
        strokeWidth: 2,
      },
    ],
    legend: ['Deposits ₹', 'Withdrawals ₹'],
  };

  return (
    <SafeAreaView className='mt-10'>
      <Text  className="text-2xl text-center font-psemibold mt-4 mb-2">
        Weekly Deposit vs Withdrawal Trends
      </Text>
      <LineChart
        data={chartData}
        width={screenWidth - 16}
        height={300}
        yAxisLabel="₹"
        verticalLabelRotation={30}
        chartConfig={{
          backgroundGradientFrom: '#fff',
          backgroundGradientTo: '#fff',
          decimalPlaces: 2,
          color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
          labelColor: () => '#333',
          propsForDots: {
            r: '4',
            strokeWidth: '1',
            stroke: '#000',
          },
        }}
        // bezier
        style={{
          marginVertical: 16,
          borderRadius: 8,
          alignSelf: 'center',
        }}
      />
    </SafeAreaView>
  );
};

export default WeeklyTrends;
