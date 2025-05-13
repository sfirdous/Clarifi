import { View, Text, Image } from 'react-native'
import { Tabs, Redirect } from 'expo-router'
import icons from "../../constants/icons.js"

const TabsLayout = () => {
    const TabIcon = ({ color, focused, name, icon }: any) => {
        return (
            <View className='justify-center items-center gap-1'>
                <Image
                    source={icon}
                    resizeMode='contain'
                    tintColor={color}
                    className='w-6 h-6' />

                <Text className={`${focused ? 'font-psemibold' : 'font-pregular'} text-xs`} style={{ color: color, fontSize: 7 }}>{name}</Text>

            </View>
        )
    }
    return (
        <>
            <Tabs
                screenOptions={{
                    tabBarShowLabel: false,
                    tabBarActiveTintColor: '#FFA001',
                    tabBarInactiveTintColor: '#CDCDE0',
                    tabBarStyle: {
                        backgroundColor: '#161622',
                        borderTopWidth: 1,
                        borderTopColor: '#232533',
                        height: 64,
                        paddingTop: 10,
                    }
                }}>
                <Tabs.Screen
                    name="home"
                    options={{
                        title: 'Home',
                        headerShown: false,
                        tabBarIcon: ({ color, focused }) => (
                            <TabIcon
                                color={color}
                                name="Home"
                                focused={focused}
                                icon={icons.home}
                            />

                        )
                    }} />

                <Tabs.Screen
                    name="statistics"
                    options={{
                        title: 'Statistics',
                        headerShown: false,
                        tabBarIcon: ({ color, focused }) => (
                            <TabIcon
                                color={color}
                                name="Statistics"
                                focused={focused}
                                icon={icons.piechart}
                            />

                        )
                    }} />

                <Tabs.Screen
                    name="weeklytrends"
                    options={{
                        title: 'Trends',
                        headerShown: false,
                        tabBarIcon: ({ color, focused }) => (
                            <TabIcon
                                color={color}
                                name="Trends"
                                focused={focused}
                                icon={icons.barchart}
                            />

                        )
                    }} />
            </Tabs>
        </>
    )
}

export default TabsLayout