const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const projectRoot = path.resolve(__dirname, '..', '..');
const dbPath = path.join(projectRoot, 'playwright-app.db');
const port = 8123;
const baseURL = `http://127.0.0.1:${port}`;

let server;

function waitForServer(url, timeout = 30000) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const tryConnect = () => {
      const http = require('http');
      const req = http.get(url, (res) => {
        res.resume();
        resolve();
      });
      req.on('error', () => {
        if (Date.now() - start > timeout) {
          reject(new Error('Server did not start in time'));
        } else {
          setTimeout(tryConnect, 500);
        }
      });
    };
    tryConnect();
  });
}

test.beforeAll(async () => {
  if (fs.existsSync(dbPath)) {
    fs.unlinkSync(dbPath);
  }

  server = spawn(
    'c:/Users/KFsil/OneDrive/Desktop/mcp-correo/.venv/Scripts/python.exe',
    ['-m', 'uvicorn', 'interfaz_web:app', '--host', '127.0.0.1', '--port', String(port)],
    {
      cwd: projectRoot,
      env: { ...process.env, APP_DB_PATH: dbPath },
      stdio: 'pipe',
    },
  );

  server.stdout.on('data', () => {});
  server.stderr.on('data', () => {});

  await waitForServer(`${baseURL}/`);
});

test.afterAll(() => {
  if (server) {
    server.kill('SIGTERM');
  }
});

test('admin can login and see dashboard', async ({ page }) => {
  await page.goto(baseURL);
  await page.locator('input[name="username"]').fill('admin');
  await page.locator('input[name="password"]').fill('admin123');
  await page.locator('button[type="submit"]').click();

  await expect(page).toHaveURL(/dashboard/);
  await expect(page.getByText('Centro de Operaciones')).toBeVisible();
  await expect(page.getByText('Estado de servicios')).toBeVisible();
});

test('admin can close the session from the dashboard', async ({ page }) => {
  await page.goto(baseURL);
  await page.locator('input[name="username"]').fill('admin');
  await page.locator('input[name="password"]').fill('admin123');
  await page.locator('button[type="submit"]').click();

  await expect(page.getByRole('link', { name: 'Cerrar sesión' })).toBeVisible();
  await page.getByRole('link', { name: 'Cerrar sesión' }).click();

  await expect(page).toHaveURL(`${baseURL}/`);
  await expect(page.locator('input[name="username"]')).toBeVisible();
  await page.goto(`${baseURL}/dashboard`);
  await expect(page).toHaveURL(`${baseURL}/`);
});

test('registration enforces strong passwords and supports special characters', async ({ page }) => {
  const weakPasswords = ['123456', 'admin123', 'password'];

  for (const [index, password] of weakPasswords.entries()) {
    await page.goto(`${baseURL}/register`);
    await page.locator('input[name="username"]').fill(`weak_${Date.now()}_${index}`);
    await page.locator('input[name="password"]').fill(password);
    await page.locator('button[type="submit"]').click();

    await expect(page).toHaveURL(/\/register/);
    await expect(page.locator('.error')).toContainText('Contraseña');
  }

  await page.goto(`${baseURL}/register`);
  await page.locator('input[name="username"]').fill(`strong_${Date.now()}`);
  await page.locator('input[name="password"]').fill('Niebla!Cobre_47#Luna');
  await page.locator('select[name="role"]').selectOption('user');
  await page.locator('button[type="submit"]').click();

  await expect(page).toHaveURL(`${baseURL}/`);
  await expect(page.locator('input[name="username"]')).toBeVisible();
});

test('admin can create and edit a user', async ({ page }) => {
  await page.goto(baseURL);
  await page.locator('input[name="username"]').fill('admin');
  await page.locator('input[name="password"]').fill('admin123');
  await page.locator('button[type="submit"]').click();

  await page.goto(`${baseURL}/admin/users`);
  await page.locator('input[name="username"]').first().fill('qa_user');
  await page.locator('input[name="password"]').first().fill('Q7!a_secure_user#42');
  await page.locator('select[name="role"]').first().selectOption('user');
  await page.locator('form[action="/admin/users"] button[type="submit"]').click();

  await expect(page.locator('text=qa_user')).toBeVisible();

  const createdUserRow = page.locator('tr').filter({ hasText: 'qa_user' });
  await createdUserRow.locator('input[name="username"]').fill('qa_user_updated');
  await createdUserRow.locator('select[name="role"]').selectOption('admin');
  await createdUserRow.locator('form[action="/admin/users/update"] button[type="submit"]').click();

  await expect(page.locator('text=qa_user_updated')).toBeVisible();
});

test('admin can navigate to logs and SMTP settings', async ({ page }) => {
  await page.goto(baseURL);
  await page.locator('input[name="username"]').fill('admin');
  await page.locator('input[name="password"]').fill('admin123');
  await page.locator('button[type="submit"]').click();

  await page.getByRole('navigation', { name: 'Navegación de operaciones' }).getByRole('link', { name: /Logs/ }).click();
  await expect(page).toHaveURL(/\/logs/);
  await expect(page.getByRole('heading', { name: 'Registro de actividad' })).toBeVisible();

  await page.getByRole('link', { name: 'Configuración' }).click();
  await expect(page).toHaveURL(/\/smtp-settings/);
  await expect(page.getByRole('heading', { name: 'Configuración SMTP' })).toBeVisible();
  await expect(page.locator('input[name="smtp_host"]')).toBeVisible();
});

test('dashboard controls are interactive', async ({ page }) => {
  await page.goto(baseURL);
  await page.locator('input[name="username"]').fill('admin');
  await page.locator('input[name="password"]').fill('admin123');
  await page.locator('button[type="submit"]').click();

  await page.locator('#theme-toggle').click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await page.locator('#mcp-test').click();
  await expect(page.locator('#mcp-result')).toContainText('MCP Server disponible');
  await page.locator('#mail-search').fill('no-match@example.com');
  await expect(page.locator('#mail-table tbody tr[data-status]')).toHaveCount(0);
});
