import { SafeAreaView, StyleSheet } from 'react-native';

import { NavigationReadView } from '@features/navigation/NavigationReadView';

export const NavigationScreen = () => (
  <SafeAreaView style={styles.container}>
    <NavigationReadView />
  </SafeAreaView>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#030712',
    padding: 16
  }
});
