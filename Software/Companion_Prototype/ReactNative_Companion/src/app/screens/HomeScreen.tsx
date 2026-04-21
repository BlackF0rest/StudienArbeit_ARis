import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { SafeAreaView, StyleSheet, Text } from 'react-native';

import { FeatureQuickLinks } from '@features/navigation/FeatureQuickLinks';
import { RootStackParamList } from '@shared/types/navigation';

type Props = NativeStackScreenProps<RootStackParamList, 'Home'>;

export const HomeScreen = ({ navigation }: Props) => (
  <SafeAreaView style={styles.container}>
    <Text style={styles.heading}>ARis Companion</Text>
    <FeatureQuickLinks navigation={navigation} />
  </SafeAreaView>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#030712',
    padding: 16,
    gap: 16
  },
  heading: {
    color: '#ffffff',
    fontSize: 28,
    fontWeight: '700'
  }
});
