import React from 'react';
import { ChatInterface } from './components/ChatInterface';
import './App.css';

function App() {
  return (
    <div className="app">
      <ChatInterface apiUrl="http://localhost:8000" />
    </div>
  );
}

export default App;
