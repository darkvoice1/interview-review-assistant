import { test, expect } from '@playwright/test'

// 首页场景主要验证真实页面渲染和导航是否正常。
test('首页可以展示统计卡片并跳转到文档页', async ({ page }) => {
  await page.route('**/api/review/stats', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        document_count: 3,
        question_count: 42,
        due_review_count: 5,
        wrong_question_count: 4,
        review_record_count: 18,
        reviewed_today_count: 2,
      }),
    })
  })

  await page.route('**/api/questions/wrong', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 1,
          chunk_id: 1,
          document_id: 1,
          section_title: 'Redis 持久化',
          question_type: 'short_answer',
          question: 'Redis 的 AOF 和 RDB 有什么区别？',
          answer: '<p>AOF 记录命令，RDB 保存快照。</p>',
          analysis: null,
          difficulty: 2,
          created_at: '2026-05-01T08:00:00Z',
          source_title: 'Redis 面试笔记',
          last_feedback: '不会',
          next_review_at: '2026-05-02T08:00:00Z',
          review_count: 2,
          mastery_level: 1,
        },
      ]),
    })
  })

  await page.route('**/api/documents', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 1,
          title: 'Redis 面试笔记',
          source_type: 'markdown',
          file_path: 'storage/documents/redis.md',
          created_at: '2026-05-01T08:00:00Z',
        },
      ]),
    })
  })

  await page.goto('/')

  const dueReviewCard = page.locator('.stat-card').filter({ hasText: '今日待复习' })
  await expect(dueReviewCard).toBeVisible()
  await expect(dueReviewCard.getByText('5', { exact: true })).toBeVisible()
  await expect(page.getByText('Redis 持久化')).toBeVisible()

  await page.getByText('管理文档').click()
  await expect(page).toHaveURL(/\/documents$/)
  await expect(page.getByText('已导入文档')).toBeVisible()
})

// 文档上传场景验证前端是否正确串联上传接口和生成题目接口。
test('文档页上传 markdown 后展示成功提示', async ({ page }) => {
  await page.route('**/api/documents', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 8,
          title: '操作系统核心概念',
          source_type: 'markdown',
          file_path: 'storage/documents/os.md',
          created_at: '2026-05-01T08:00:00Z',
        },
      ]),
    })
  })

  await page.route('**/api/documents/upload', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 9,
        title: '新上传的面经',
        source_type: 'markdown',
        file_path: 'storage/documents/new.md',
        created_at: '2026-05-01T08:30:00Z',
        chunk_count: 3,
        section_count: 3,
      }),
    })
  })

  await page.route('**/api/questions/generate/9', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        document_id: 9,
        chunk_count: 3,
        generated_question_count: 3,
        skipped_chunk_count: 0,
      }),
    })
  })

  await page.goto('/documents')

  await page.locator('input[type="file"]').setInputFiles({
    name: 'demo.md',
    mimeType: 'text/markdown',
    buffer: Buffer.from('# Redis\n\n- AOF\n'),
  })

  await expect(page.getByText('成功上传 1 个文件，并已自动生成题目。')).toBeVisible()
})

// 今日复习场景验证前端是否能加载题目、展开答案并提交反馈。
test('复习页可以查看答案并提交复习结果', async ({ page }) => {
  await page.route('**/api/review/today', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total: 1,
        items: [
          {
            question_id: 11,
            question: '什么是 B+ 树索引？',
            difficulty: 2,
            due_at: '2026-05-01T09:00:00Z',
            source_title: 'MySQL 高频问题',
          },
        ],
      }),
    })
  })

  await page.route('**/api/questions/11', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 11,
        chunk_id: 3,
        document_id: 2,
        section_title: 'MySQL 索引',
        question_type: 'short_answer',
        question: '什么是 B+ 树索引？',
        answer: '<p>B+ 树把数据集中在叶子节点。</p>',
        analysis: '它适合范围查询。',
        difficulty: 2,
        created_at: '2026-05-01T08:00:00Z',
        source_title: 'MySQL 高频问题',
        source_type: 'markdown',
        chunk_content: 'B+ 树的叶子节点之间是有序链表。',
        review_count: 1,
        correct_streak: 0,
        mastery_level: 1,
        last_review_at: '2026-04-30T08:00:00Z',
        next_review_at: '2026-05-01T09:00:00Z',
        last_feedback: '不会',
      }),
    })
  })

  await page.route('**/api/review/submit', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        question_id: 11,
        user_feedback: '会',
        review_time: '2026-05-01T09:05:00Z',
        next_review_at: '2026-05-08T09:05:00Z',
        review_count: 2,
        correct_streak: 1,
        mastery_level: 3,
      }),
    })
  })

  await page.goto('/review')

  await expect(page.getByText('什么是 B+ 树索引？')).toBeVisible()
  await page.getByText('查看答案').click()
  await expect(page.getByText('B+ 树把数据集中在叶子节点。')).toBeVisible()
  await page.getByRole('button', { name: '会', exact: true }).click()
  await expect(page.getByText('已记录“会”')).toBeVisible()
})
