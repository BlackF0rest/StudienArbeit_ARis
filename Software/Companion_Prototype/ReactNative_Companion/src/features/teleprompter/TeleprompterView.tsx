import { ScrollView, StyleSheet, Text, View } from 'react-native';

const DEFAULT_SCRIPT = [
  'Willkommen im ARis Companion.',
  'Verbindung aufbauen und Status prüfen.',
  'Teleprompter-Ansicht für Moderation nutzen.'
];

export const TeleprompterView = () => (
  <View style={styles.container}>
    <Text style={styles.title}>Teleprompter</Text>
    <ScrollView style={styles.scriptContainer}>
      {DEFAULT_SCRIPT.map(line => (
        <Text key={line} style={styles.scriptLine}>
          {line}
        </Text>
      ))}
    </ScrollView>
  </View>
);

const styles = StyleSheet.create({
  container: {
    gap: 12,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#111827',
    flex: 1
  },
  title: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: '600'
  },
  scriptContainer: {
    maxHeight: 220
  },
  scriptLine: {
    color: '#e5e7eb',
    fontSize: 18,
    lineHeight: 28,
    marginBottom: 8
  }
});
