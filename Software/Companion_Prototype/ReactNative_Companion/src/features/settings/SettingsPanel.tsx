import { StyleSheet, Switch, Text, View } from 'react-native';

import { useState } from 'react';

export const SettingsPanel = () => {
  const [darkMode, setDarkMode] = useState(true);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Settings</Text>
      <View style={styles.row}>
        <Text style={styles.label}>Dark mode</Text>
        <Switch value={darkMode} onValueChange={setDarkMode} />
      </View>
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
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  label: {
    color: '#d1d5db',
    fontSize: 16
  }
});
