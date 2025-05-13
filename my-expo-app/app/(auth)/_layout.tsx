// This file is used to create a layout for the authentication screens
// It uses the Stack component from expo-router to create a stack navigator
// It contains two screens: sign-in and sign-up
// Both screens have their headers hidden
// The StatusBar component is used to set the background color and style of the status bar
// The layout is exported as AuthLayout
// The layout is used in the authentication screens to provide a consistent look and feel
import { Stack } from 'expo-router'
import React from 'react'
import { StatusBar } from 'expo-status-bar'

const AuthLayout = () => {
  return (
    <>
      <Stack>
        <Stack.Screen
          name='sign-in'
          options={{
            headerShown: false
          }} />
           <Stack.Screen
          name='sign-up'
          options={{
            headerShown: false
          }} />
      </Stack>
      <StatusBar
      backgroundColor='#161622'
      style='light'
      />
     
    </>
  )
}

export default AuthLayout