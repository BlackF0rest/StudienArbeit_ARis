import { SafeAreaView, StyleSheet } from 'react-native';

import { ConnectionPanel } from '@features/connection/ConnectionPanel';

export const ConnectionScreen = () => (
  <SafeAreaView style={styles.container}>
    <ConnectionPanel />
  </SafeAreaView>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#030712',
    padding: 16
  }
});
