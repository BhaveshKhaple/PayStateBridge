import { test, expect } from '@playwright/test'

test.describe('Mobile viewport (360px)', () => {
  test.use({ viewport: { width: 360, height: 800 } })

  test('home page renders at 360px', async ({ page }) => {
    await page.goto('http://localhost:3000')
    await expect(page.locator('h1')).toContainText('PayState Bridge')
  })

  test('cases list renders at 360px', async ({ page }) => {
    await page.goto('http://localhost:3000/cases')
    await expect(page.locator('h2')).toContainText('Payment Cases')
  })
})
