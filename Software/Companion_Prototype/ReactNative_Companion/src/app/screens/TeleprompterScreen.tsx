import { SafeAreaView, StyleSheet } from 'react-native';

import { TeleprompterView } from '@features/teleprompter/TeleprompterView';

export const TeleprompterScreen = () => (
  <SafeAreaView style={styles.container}>
    <TeleprompterView />
  </SafeAreaView>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#030712',
    padding: 16
  }
});
