import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, Dimensions } from 'react-native';
import { PieChart, BarChart } from 'react-native-chart-kit';
import { getStats } from '../../utils/api';


const screenWidth = Dimensions.get('window').width;

const chartConfig = {
  backgroundGradientFrom: "#fff",
  backgroundGradientTo: "#fff",
  decimalPlaces: 2,
  color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
  labelColor: () => '#333',
};

// 1. Define the shape of the stats data
interface StatsData {
  total_withdrawals: number;
  total_deposits: number;
  category_wise_spending: { [category: string]: number };
  essential_vs_nonessential: { [key: string]: number };
  income_vs_expense_ratio: number;
}

const Statistics = () => {
  const [stats, setStats] = useState<StatsData | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getStats();
        setStats(data);
      } catch (error) {
        console.error('Error fetching stats:', error);
      }
    };
    fetchStats();
  }, []);

  if (!stats) return <Text className="text-center mt-10">Loading statistics...</Text>;

  const categoryData = Object.entries(stats.category_wise_spending).map(([key, value], index) => ({
    name: key,
    amount: value,
    color: ['#f39c12', '#e74c3c', '#2ecc71', '#3498db'][index % 4],
    legendFontColor: '#333',
    legendFontSize: 14,
  }));

  return (
    // <SafeAreaView className='bg-primary h-full px-4 items-center justify-center'>
    
    <ScrollView className="p-4 mt-10">
      <Text className="text-xl font-psemibold mb-2">Total Withdrawals: ₹{stats.total_withdrawals.toFixed(2)}</Text>
      <Text className="text-xl font-psemibold mb-4">Total Deposits: ₹{stats.total_deposits.toFixed(2)}</Text>

      <Text className="text-lg font-psemibold mt-4 mb-2">Spending by Category</Text>
      <PieChart
        data={categoryData}
        width={screenWidth - 32}
        height={220}
        chartConfig={chartConfig}
        accessor="amount"
        backgroundColor="transparent"
        paddingLeft="15"
        absolute
      />

      <Text className="text-lg font-psemibold mt-6 mb-2">Essential vs Non-Essential</Text>
      <BarChart
        data={{
          labels: Object.keys(stats.essential_vs_nonessential),
          datasets: [{ data: Object.values(stats.essential_vs_nonessential) }],
        }}
        width={screenWidth - 32}
        height={220}
        yAxisLabel="₹"
        yAxisSuffix=""
        chartConfig={chartConfig}
        verticalLabelRotation={0}
        fromZero
      />

      <Text className="text-lg font-psemibold mt-6">
        Income to Expense Ratio: {stats.income_vs_expense_ratio.toFixed(2)}
      </Text>
    </ScrollView>
    // </SafeAreaView>
  );
};

export default Statistics;
