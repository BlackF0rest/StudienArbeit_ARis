import { StatusBar } from 'expo-status-bar';

import { RootNavigator } from '@app/navigation/RootNavigator';

const App = () => (
  <>
    <StatusBar style="light" />
    <RootNavigator />
  </>
);

export default App;
