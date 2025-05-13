import { useState } from "react";
import { Link, router } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";
import { View, Text, ScrollView, Dimensions, Alert, Image } from "react-native";

import { Picker } from "@react-native-picker/picker";
import CustomButton from "../../components/CustomButton";
import FormField from "../../components/FormField"
import api from '../../utils/api'; 



const SignUp = () => {
  // const { setUser, setIsLogged } = useGlobalContext();
  const [isSubmitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    bank_name: ""
  });

  const submit = async () => {

    if (!form.username || !form.email || !form.password || !form.bank_name) {
      Alert.alert("Error", "Please fill all fields.");
      return;
    }
  
    setSubmitting(true);
    try {
      const response = await api.post('/register', form);
      Alert.alert("Success", "Account created. Please sign in.");
      router.replace('/sign-in');
    } catch (error: any) {
      console.log('Error response:', error.response?.data); // Log backend error
      console.log('Error message:', error.message); // Log general error message
      Alert.alert("Registration Failed", error.response?.data?.detail || "Something went wrong.");
    } finally {
      setSubmitting(false);
    }

  };

  return (
    <SafeAreaView className="bg-primary h-full">
      <ScrollView>
        <View
          className="w-full flex justify-center h-full px-4 my-6"
          style={{
            minHeight: Dimensions.get("window").height - 100,
          }}
        >
          {/* <Image
            source={images.logo}
            resizeMode="contain"
            className="w-[115px] h-[34px]"
          /> */}

          <Text className="text-2xl font-semibold text-white mt-10 font-psemibold">
            SignUp to Clarifi
          </Text>

          <FormField
            title="Username"
            value={form.username}
            handleChangeText={(e : any) => setForm({ ...form, username: e })}
            otherStyles="mt-10"
          />
          
          <FormField
            title="Email"
            value={form.email}
            handleChangeText={(e: any) => setForm({ ...form, email: e })}
            otherStyles="mt-7"
            keyboardType="email-address"
          />

          <FormField
            title="Password"
            value={form.password}
            handleChangeText={(e: any) => setForm({ ...form, password: e })}
            otherStyles="mt-7"
          />

          <View className="space-y-10 mt-7">
            {/* <Text className="text-base font-psemibold text-gray-400">Select Bank</Text> */}
            <View className="w-full bg-black-100 h-16 px-4 border-black-200 rounded-md justify-center">
              <Picker
                selectedValue={form.bank_name}
                onValueChange={(itemValue) =>
                  setForm({ ...form, bank_name: itemValue })
                }
                dropdownIconColor="#ffffff"
                style={{
                  color: '#ffffff',
                  backgroundColor: 'transparent',
                
                }}
              >
                <Picker.Item label="Choose Bank" value="" />
                <Picker.Item label="HDFC" value="HDFC" />
                <Picker.Item label="SBI" value="SBI" />
                <Picker.Item label="ICICI" value="ICICI" />
              </Picker>
            </View>
          </View>




          <CustomButton
            title="Sign Up"
            handlePress={submit}
            containerStyles="mt-7"
            isLoading={isSubmitting}
          />

          <View className="flex justify-center pt-5 flex-row gap-2">
            <Text className="text-lg text-gray-100 font-pregular">
              Have an account already?
            </Text>
            <Link
              href="/sign-in"
              className="text-lg font-psemibold text-secondary"
            >
              SignIn
            </Link>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

export default SignUp;


