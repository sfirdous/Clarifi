import { useState } from "react";
import { Link, router } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";
import { View, Text, ScrollView, Dimensions, Alert, Image } from "react-native";

import CustomButton from "../../components/CustomButton";
import FormField from "../../components/FormField";

import api from '../../utils/api';
import AsyncStorage from '@react-native-async-storage/async-storage';


const SignIn = () => {
  // const { setUser, setIsLogged } = useGlobalContext();
  const [isSubmitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const submit = async () => {
    if (!form.email || !form.password) {
      Alert.alert("Error", "Please enter email and password.");
      return;
    }

    setSubmitting(true);
    try {
      const response = await api.post('/login', {
        email: form.email,
        password: form.password,
      });

      const { user_id, username, email, bank_name } = response.data;


      // ✅ Save to AsyncStorage
      await AsyncStorage.multiSet([
        ['user_id', user_id],
        ['username', username],
        ['email', email],
        ['bank_name', bank_name],
      ]);
      // Save token (AsyncStorage or context)
      Alert.alert("Login Successful");
      router.replace('/home'); // or your home screen
    } catch (error: any) {
      Alert.alert("Login Failed", error.response?.data?.detail || "Invalid credentials.");
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
            Log in to Clarifi
          </Text>

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

          <CustomButton
            title="Sign In"
            handlePress={submit}
            containerStyles="mt-7"
            isLoading={isSubmitting}
          />

          <View className="flex justify-center pt-5 flex-row gap-2">
            <Text className="text-lg text-gray-100 font-pregular">
              Don't have an account?
            </Text>
            <Link
              href="/sign-up"
              className="text-lg font-psemibold text-secondary"
            >
              Signup
            </Link>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

export default SignIn;


