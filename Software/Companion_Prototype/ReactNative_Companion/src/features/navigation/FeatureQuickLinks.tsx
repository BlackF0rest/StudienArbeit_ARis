import { Pressable, StyleSheet, Text, View } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { RootStackParamList } from '@shared/types/navigation';

type QuickLinksProps = {
  navigation: NativeStackNavigationProp<RootStackParamList>;
};

export const FeatureQuickLinks = ({ navigation }: QuickLinksProps) => (
  <View style={styles.container}>
    <Text style={styles.title}>Schnellzugriff</Text>
    {['Connection', 'Navigation', 'Teleprompter', 'Settings'].map(route => (
      <Pressable
        key={route}
        onPress={() => navigation.navigate(route as keyof RootStackParamList)}
        style={styles.link}
      >
        <Text style={styles.linkLabel}>{route}</Text>
      </Pressable>
    ))}
  </View>
);

const styles = StyleSheet.create({
  container: {
    gap: 8,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#1f2937'
  },
  title: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 18
  },
  link: {
    backgroundColor: '#2563eb',
    borderRadius: 8,
    padding: 10
  },
  linkLabel: {
    color: '#ffffff',
    fontSize: 15
  }
});
