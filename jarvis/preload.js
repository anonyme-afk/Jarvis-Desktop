const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('jarvis', {
  sendMessage: (message) => ipcRenderer.invoke('send-message', message),
  toggleMic: (enabled) => ipcRenderer.invoke('toggle-mic', enabled),
  analyzeCamera: () => ipcRenderer.invoke('analyze-camera'),
  analyzeScreen: () => ipcRenderer.invoke('analyze-screen'),
  openUrl: (url) => ipcRenderer.invoke('open-url', url),
  systemAction: (action, params) => ipcRenderer.invoke('system-action', action, params),
  
  onPythonLog: (callback) => ipcRenderer.on('python-log', (event, data) => callback(data)),
  onJarvisResponse: (callback) => ipcRenderer.on('jarvis-response', (event, data) => callback(data)),
  onTranscription: (callback) => ipcRenderer.on('transcription', (event, text) => callback(text))
});
