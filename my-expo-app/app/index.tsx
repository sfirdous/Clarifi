import { StatusBar } from 'expo-status-bar';
import { Text ,View,ScrollView,Image} from 'react-native';
import {Redirect,router} from 'expo-router'
import { SafeAreaView } from 'react-native-safe-area-context';
import {images} from '../constants'
import CustomButton from '../components/CustomButton';


export default function App() {
  return (
  <SafeAreaView className='bg-primary h-full'>
    <ScrollView contentContainerStyle={{height :'100%'}}>
    <View className='w-full h-full justify-center items-center px-4'>
          <Image
            source={images.logo}
            className='h-[150px] w-[150px]'
            resizeMode='contain' />
          {/* <Image
            source={images.cards}
            className='max-w-[380px] w-full h-[300px]'
            resizeMode='contain' /> */}
        
          <CustomButton
            title="Continue with Email"
            handlePress={() => router.push('/(auth)/sign-in')}
            containerStyles=" mt-7"

          />

        </View>

    </ScrollView>
    <StatusBar backgroundColor='#161622' style='light'/>

  </SafeAreaView>
  );
}

