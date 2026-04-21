import { SafeAreaView, StyleSheet } from 'react-native';

import { SettingsPanel } from '@features/settings/SettingsPanel';

export const SettingsScreen = () => (
  <SafeAreaView style={styles.container}>
    <SettingsPanel />
  </SafeAreaView>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#030712',
    padding: 16
  }
});
