import { SafeAreaView } from 'react-native-safe-area-context'
import * as DocumentPicker from 'expo-document-picker'
import CustomButton from '../../components/CustomButton'
import api from '../../utils/api'
import AsyncStorage from '@react-native-async-storage/async-storage';

const Home = () => {
  const handleUpload = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: 'application/pdf',
        copyToCacheDirectory: true,
      });

      if (result.assets && result.assets.length > 0) {
        const pdf = result.assets[0];
        console.log('PDF selected:', pdf);

        const userId = await AsyncStorage.getItem('user_id');
        if (!userId) {
          alert('User not logged in');
          return;
        }

        const formData = new FormData();
        formData.append('file', {
          uri: pdf.uri,
          name: pdf.name,
          type: 'application/pdf',
        } as any); // 👈 Type workaround

        const response = await fetch(
          `${api.defaults.baseURL}/upload-pdf/?user_id=${userId}`,
          {
            method: 'POST',
            body: formData,
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        );

        const data = await response.json();
       


        if (!response.ok) {
          throw new Error(data.detail || 'Upload failed');
        }

        console.log('Upload success:', data);
        alert(`Uploaded! PDF ID: ${data.pdf_id}`);

        // Save the PDF ID to AsyncStorage
        await AsyncStorage.setItem('pdf_id', data.pdf_id);

        // Optional:  navigate to another screen here, if needed
      }
    } catch (error) {
      console.error('Upload failed:', error);
      if (error instanceof Error) {
        alert(`Upload failed: ${error.message}`);
      } else {
        alert('Upload failed: An unknown error occurred');
      }
    }
  };


  return (
    <SafeAreaView className='bg-primary h-full px-4 items-center justify-center'>

      <CustomButton
        title="Upload PDF"
        handlePress={handleUpload}
        containerStyles=""
        textStyles=""
        isLoading={false}
      />
    </SafeAreaView>
  );
};

export default Home;
