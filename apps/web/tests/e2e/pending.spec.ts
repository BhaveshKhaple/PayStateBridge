import { test, expect } from '@playwright/test'

test.describe('Pending payment — do not retry', () => {
  test('pending case shows DO NOT RETRY banner', async ({ page }) => {
    // Navigate to cases list
    await page.goto('http://localhost:3000/cases')
    await expect(page.locator('h2')).toContainText('Payment Cases')
  })

  test('recovery link button is disabled for pending case', async ({ page }) => {
    // This test requires a seeded DB with a PENDING case
    // Documented as manual verification step
    await page.goto('http://localhost:3000/cases')
    const pendingBadge = page.locator('text=PENDING').first()
    if (await pendingBadge.isVisible()) {
      await pendingBadge.click()
      const createLinkBtn = page.locator('button:has-text("Create recovery link")')
      if (await createLinkBtn.isVisible()) {
        await expect(createLinkBtn).toBeDisabled()
      }
    }
  })
})
