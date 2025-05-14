import { TouchableOpacity, Text } from 'react-native'
import React from 'react'

const CustomButton= ({title,handlePress,containerStyles,textStyles,isLoading} : any) => {
  return (
    <TouchableOpacity 
     className={`justify-center items-center bg-secondary w-full  mt-7 min-h-[60px] rounded-xl ${containerStyles} ${isLoading ? 'opacity-50': ''}`}
    onPress={handlePress}
    activeOpacity={0.7}
    disabled={isLoading}>
        <Text className={`text-primary font-psemibold text-xl ${textStyles}`}>{title}</Text>
    </TouchableOpacity>
  )
}

export default CustomButton