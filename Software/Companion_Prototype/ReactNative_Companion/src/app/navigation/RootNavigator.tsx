import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import { ConnectionScreen } from '@app/screens/ConnectionScreen';
import { HomeScreen } from '@app/screens/HomeScreen';
import { SettingsScreen } from '@app/screens/SettingsScreen';
import { TeleprompterScreen } from '@app/screens/TeleprompterScreen';
import { RootStackParamList } from '@shared/types/navigation';

const Stack = createNativeStackNavigator<RootStackParamList>();

const appTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    background: '#030712'
  }
};

export const RootNavigator = () => (
  <NavigationContainer theme={appTheme}>
    <Stack.Navigator
      initialRouteName="Home"
      screenOptions={{
        headerStyle: { backgroundColor: '#030712' },
        headerTintColor: '#ffffff',
        contentStyle: { backgroundColor: '#030712' }
      }}
    >
      <Stack.Screen name="Home" component={HomeScreen} />
      <Stack.Screen name="Connection" component={ConnectionScreen} />
      <Stack.Screen name="Teleprompter" component={TeleprompterScreen} />
      <Stack.Screen name="Settings" component={SettingsScreen} />
    </Stack.Navigator>
  </NavigationContainer>
);
