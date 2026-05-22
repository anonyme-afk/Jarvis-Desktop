const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
require('dotenv').config();

let mainWindow;
let pythonProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    backgroundColor: '#040D1A',
    titleBarStyle: 'hidden',
    titleBarOverlay: {
      color: '#040D1A',
      symbolColor: '#00D4FF',
      height: 30
    },
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    },
    icon: path.join(__dirname, 'assets/icon.png'),
    show: false
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer/index.html'));

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  startPythonServer();
}

function startPythonServer() {
  const pythonExecutable = process.platform === 'win32' ? 'python' : 'python3';
  pythonProcess = spawn(pythonExecutable, [
    path.join(__dirname, 'python/server.py')
  ], {
    env: { ...process.env }
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log('[Python]', data.toString());
    if (mainWindow) mainWindow.webContents.send('python-log', data.toString());
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error('[Python Error]', data.toString());
  });
}

ipcMain.handle('send-message', async (event, message) => {
  return new Promise((resolve, reject) => {
    const http = require('http');
    const body = JSON.stringify({ message });
    const req = http.request({
      hostname: '127.0.0.1', port: 5001,
      path: '/chat', method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) }
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(JSON.parse(data)));
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
});

ipcMain.handle('toggle-mic', async (event, enabled) => {
  return { success: true };
});

ipcMain.handle('analyze-camera', async () => {
  return new Promise((resolve, reject) => {
    const http = require('http');
    const req = http.request({
      hostname: '127.0.0.1', port: 5001,
      path: '/vision', method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(JSON.parse(data)));
    });
    req.on('error', reject);
    req.write(JSON.stringify({question: "Qu'est ce que tu vois ?"}));
    req.end();
  });
});

ipcMain.handle('analyze-screen', async () => {
  return new Promise((resolve, reject) => {
    const http = require('http');
    const req = http.request({
      hostname: '127.0.0.1', port: 5001,
      path: '/vision/screen', method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(JSON.parse(data)));
    });
    req.on('error', reject);
    req.write(JSON.stringify({question: "Décris ce qui se trouve sur ce screenshot de mon écran d'ordinateur."}));
    req.end();
  });
});

ipcMain.handle('open-url', async (event, url) => {
  await shell.openExternal(url);
  return { success: true };
});

ipcMain.handle('system-action', async (event, action, params) => {
  return { success: true };
});

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (pythonProcess) pythonProcess.kill();
  if (process.platform !== 'darwin') app.quit();
});
