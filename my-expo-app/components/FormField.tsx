import { View, Text, TextInput, TouchableOpacity, Image } from 'react-native'
import React, { useState } from 'react'
import { icons } from '../constants'

const FormField = ({ title, otherStyles, value, handleChangeText, ...props } :any) => {
  const [showPassword, setShowPassword] = useState(false)
  
  return (
    <View className={`space-y-10 ${otherStyles}`}>
      <Text className={`text-base font-psemibold text-gray-400`}>{title}</Text>
      <View className={`w-full bg-black-100 h-16 px-4 mt-2 border-black-200  rounded-md focus:border-secondary-200 items-center flex-row`}>
        <TextInput
          className={`h-full text-base  flex-1 font-pmedium text-white`}
          value={value}
          // placeholder={placeholder}
          placeholderTextColor='#7b7b8b'
          onChangeText={handleChangeText}
          secureTextEntry={title === 'Password' && !showPassword} />
        {title === 'Password' && (
          <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
            <Image source={!showPassword ? icons.eye : icons.eyeHide} className='w-6 h-6' resizeMode='contain'/>
          </TouchableOpacity>
        )}
      </View>

    </View>
  )
}

export default FormField