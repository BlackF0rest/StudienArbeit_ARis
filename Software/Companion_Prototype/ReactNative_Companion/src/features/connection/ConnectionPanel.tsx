import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useConnectionState } from '@shared/state/store';

export const ConnectionPanel = () => {
  const { state, setState } = useConnectionState();

  const handleToggleConnection = () => {
    setState(prev => (prev === 'connected' ? 'disconnected' : 'connected'));
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Connection</Text>
      <Text style={styles.status}>Status: {state}</Text>
      <Pressable style={styles.button} onPress={handleToggleConnection}>
        <Text style={styles.buttonLabel}>Toggle Connection</Text>
      </Pressable>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    gap: 12,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#111827'
  },
  title: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: '600'
  },
  status: {
    color: '#d1d5db',
    fontSize: 16
  },
  button: {
    backgroundColor: '#2563eb',
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
    alignItems: 'center'
  },
  buttonLabel: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600'
  }
});
