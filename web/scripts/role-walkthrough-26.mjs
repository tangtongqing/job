import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const FRONTEND = process.env.WALKTHROUGH_FRONTEND || "http://127.0.0.1:3100";
const API = process.env.WALKTHROUGH_API || "http://127.0.0.1:8100/api/v1";
const outputDir = path.resolve(process.cwd(), "..", "output", "role-walkthrough");

const results = [];

function record(role, task, satisfied, observation) {
  results.push({
    role,
    task,
    result: satisfied ? "满足" : "未满足",
    observation,
  });
}

function includesAll(text, values) {
  return values.every((value) => text.includes(value));
}

async function apiJson(request, endpoint, options = {}) {
  const response = await request.fetch(`${API}${endpoint}`, options);
  if (!response.ok()) {
    throw new Error(`${options.method || "GET"} ${endpoint} returned ${response.status()}: ${await response.text()}`);
  }
  return response.json();
}

async function resetDemo(request) {
  return apiJson(request, "/demo/reset", { method: "POST" });
}

async function pageText(page) {
  return page.locator("body").innerText();
}

async function waitForApi(page, endpoint, action, method) {
  const responsePromise = page.waitForResponse((response) => {
    const sameEndpoint = response.url().includes(endpoint);
    const sameMethod = !method || response.request().method() === method;
    return sameEndpoint && sameMethod;
  });
  await action();
  const response = await responsePromise;
  if (!response.ok()) {
    throw new Error(`${response.request().method()} ${endpoint} returned ${response.status()}`);
  }
  return response;
}

async function runP1(browser) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  const request = context.request;
  await resetDemo(request);

  await page.goto(`${FRONTEND}/jobs`);
  await page.getByPlaceholder("产品经理、AI、增长…").fill("AI 策略产品经理");
  await page.getByPlaceholder("输入公司名称").fill("字节跳动");
  await page.getByPlaceholder("北京、上海、深圳…").fill("北京");
  const targetLink = page.getByRole("link", { name: "AI 策略产品经理", exact: true });
  await targetLink.waitFor();
  const resultText = await pageText(page);
  record(
    "P1 高频跨平台维护者",
    "使用关键词、公司和地点定位目标岗位",
    (await targetLink.count()) === 1 && resultText.includes("1 个有效岗位"),
    "三项条件收敛到字节跳动的唯一岗位"
  );

  await targetLink.click();
  await page.waitForURL("**/jobs/13");
  await page.waitForLoadState("networkidle");
  const detailText = await pageText(page);
  const targetJob = await apiJson(request, "/jobs/13");
  record(
    "P1 高频跨平台维护者",
    "核对截止时间、最后核验和来源边界",
    Boolean(targetJob.data?.deadline && targetJob.data?.last_verified_at && targetJob.data?.source) &&
      includesAll(detailText, ["截止时间", "最后核验", "来源", "不代表官方当前仍在招聘"]),
    "详情页同时展示时效字段和演示快照边界"
  );

  await page.goto(`${FRONTEND}/jobs`);
  await page.getByPlaceholder("产品经理、AI、增长…").fill("AI 策略产品经理");
  const row = page.locator("tr").filter({ hasText: "AI 策略产品经理" });
  await row.waitFor();
  await waitForApi(page, "/jobs/13/favorite", () => row.getByRole("button", { name: "收藏", exact: true }).click(), "POST");
  const favoritesAfterSave = await apiJson(request, "/user/favorites?page_size=100");
  record(
    "P1 高频跨平台维护者",
    "收藏目标岗位",
    favoritesAfterSave.data?.some((item) => item.job_id === 13),
    "收藏按钮在接口成功后切换为已收藏"
  );

  await waitForApi(page, "/jobs/13/to-apply", () => row.getByRole("button", { name: "加入待投递", exact: true }).click(), "POST");
  const toApplyAfterSave = await apiJson(request, "/user/to-apply?page_size=100");
  record(
    "P1 高频跨平台维护者",
    "加入待投递",
    toApplyAfterSave.data?.some((item) => item.job_id === 13) &&
      favoritesAfterSave.data?.some((item) => item.job_id === 13),
    "岗位同时保留收藏和待投递意图"
  );

  await page.goto(`${FRONTEND}/saved`);
  await page.getByRole("tab", { name: /待投递/ }).click();
  const savedCard = page.locator("article").filter({ hasText: "字节跳动" }).filter({ hasText: "AI 策略产品经理" });
  await savedCard.waitFor();
  record(
    "P1 高频跨平台维护者",
    "在待投递清单找回岗位",
    includesAll(await savedCard.innerText(), ["字节跳动", "AI 策略产品经理"]),
    "待投递列表可找回刚才的岗位"
  );

  await waitForApi(page, "/applications", () => savedCard.getByRole("button", { name: "创建投递", exact: true }).click(), "POST");
  await page.waitForURL(/\/applications\/\d+$/);
  const applicationUrl = page.url();
  const applicationId = Number(applicationUrl.split("/").at(-1));
  const application = await apiJson(request, `/applications/${applicationId}`);
  const initialEvents = await apiJson(request, `/applications/${applicationId}/events`);
  record(
    "P1 高频跨平台维护者",
    "创建正式投递记录",
    application.data?.status === "applied" && initialEvents.data?.some((event) => event.to_status === "applied"),
    "创建投递后写入 applied 初始事件"
  );

  const notice = "字节跳动 AI 策略产品经理面试通知：面试安排在2026年8月2日10:30，请提前进入会议。";
  await page.getByPlaceholder("粘贴招聘邮件或消息文本...").fill(notice);
  await waitForApi(page, "/applications/parse-email", () => page.getByRole("button", { name: "AI 解析", exact: true }).click(), "POST");
  const parsedText = await pageText(page);
  record(
    "P1 高频跨平台维护者",
    "粘贴招聘通知并获得状态建议",
    includesAll(parsedText, ["解析结果", "建议状态", "面试中", "计划时间", "2026"]),
    "解析结果展示建议状态、置信度和计划时间，等待人工确认"
  );

  const confirmButton = page.getByRole("button", { name: /确认将投递.*面试中.*加入近期安排/ });
  const transitionResponse = await waitForApi(
    page,
    `/applications/${applicationId}/transition`,
    () => confirmButton.click(),
    "POST"
  );
  const transitionResult = await transitionResponse.json();
  const eventsAfterConfirm = await apiJson(request, `/applications/${applicationId}/events`);
  record(
    "P1 高频跨平台维护者",
    "确认后更新状态并写入时间线",
    applicationId > 0 &&
      transitionResult.data?.application?.status === "interviewing" &&
      eventsAfterConfirm.data?.some((event) => event.to_status === "interviewing"),
    "人工确认后状态流转与历史事件同时保留"
  );

  const scheduledEvent = eventsAfterConfirm.data?.find(
    (event) => event.event_type === "interview" && event.scheduled_at
  );
  await page.goto(`${FRONTEND}/todo`);
  const todoText = await pageText(page);
  const todo = await apiJson(request, "/todo?days=14");
  record(
    "P1 高频跨平台维护者",
    "将通知里的面试时间写入近期安排",
    Boolean(scheduledEvent && transitionResult.data?.scheduled_event) &&
      todo.data?.some((item) => item.application_id === applicationId && item.event_type === "interview") &&
      includesAll(todoText, ["字节跳动", "AI 策略产品经理", "面试"]),
    "同一计划事件出现在时间线与近期安排"
  );

  await mkdir(outputDir, { recursive: true });
  await page.screenshot({
    path: path.join(outputDir, "post-fix-p1-schedule.png"),
    fullPage: true,
  });
  await context.close();
}

async function runP2(browser) {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  const request = context.request;
  await resetDemo(request);

  await page.goto(`${FRONTEND}/jobs`);
  await page.getByPlaceholder("产品经理、AI、增长…").fill("智能硬件产品实习生");
  await page.getByPlaceholder("输入公司名称").fill("小米");
  await page.getByPlaceholder("北京、上海、深圳…").fill("北京");
  const mobileTarget = page.getByRole("link", { name: "智能硬件产品实习生", exact: true }).first();
  await mobileTarget.waitFor();
  record(
    "P2 定向机会监控者",
    "移动端按岗位、公司和地点定位目标",
    (await mobileTarget.count()) >= 1 && (await pageText(page)).includes("1 个有效岗位"),
    "390px 视口下三项条件可收敛到目标岗位"
  );

  const filterText = await page.locator('[aria-label="岗位筛选"]').innerText();
  record(
    "P2 定向机会监控者",
    "按毕业年份、每周实习天数筛选",
    includesAll(filterText, ["毕业年份", "每周实习天数"]),
    "当前筛选器仍只有岗位、公司和地点"
  );

  await mobileTarget.click();
  await page.waitForURL("**/jobs/4");
  await page.waitForLoadState("networkidle");
  const internshipDetail = await pageText(page);
  const internshipJob = await apiJson(request, "/jobs/4");
  record(
    "P2 定向机会监控者",
    "核对毕业年份、学历和截止时间",
    Boolean(internshipJob.data?.graduation_year && internshipJob.data?.education && internshipJob.data?.deadline) &&
      includesAll(internshipDetail, ["毕业年份", "学历", "截止时间"]),
    "详情页已展示三项结构化信息"
  );
  record(
    "P2 定向机会监控者",
    "核对每周实习天数和实习周期",
    includesAll(internshipDetail, ["每周实习天数", "实习周期"]),
    "详情页仍无对应结构化字段"
  );

  await page.goto(`${FRONTEND}/jobs`);
  await page.getByPlaceholder("产品经理、AI、增长…").fill("智能硬件产品实习生");
  const mobileCard = page.locator("article").filter({ hasText: "智能硬件产品实习生" }).first();
  await mobileCard.waitFor();
  await waitForApi(page, "/jobs/4/favorite", () => mobileCard.getByRole("button", { name: "收藏", exact: true }).click(), "POST");
  const applications = await apiJson(request, "/applications");
  record(
    "P2 定向机会监控者",
    "只收藏、不形成投递承诺",
    applications.data?.length === 5 &&
      await mobileCard.getByRole("button", { name: "已收藏", exact: true }).isVisible(),
    "收藏后投递总数保持为标准数据的 5 条"
  );

  await page.goto(`${FRONTEND}/saved`);
  const favoriteCard = page.locator("article").filter({ hasText: "智能硬件产品实习生" }).first();
  await favoriteCard.waitFor();
  record(
    "P2 定向机会监控者",
    "在移动端收藏清单找回岗位",
    includesAll(await favoriteCard.innerText(), ["小米", "智能硬件产品实习生"]),
    "390px 视口下可在收藏页找回目标"
  );

  await page.goto(`${FRONTEND}/subscriptions`);
  await page.getByPlaceholder("如：AI 产品经理").fill("智能硬件产品");
  await page.getByPlaceholder("如：MiniMax").fill("小米");
  await page.getByPlaceholder("如：北京").fill("北京");
  const createdSubscriptionResponse = await waitForApi(
    page,
    "/subscriptions",
    () => page.getByRole("button", { name: "创建规则", exact: true }).click(),
    "POST"
  );
  const createdSubscription = await createdSubscriptionResponse.json();
  const subscriptionText = await pageText(page);
  record(
    "P2 定向机会监控者",
    "创建目标公司岗位订阅",
    createdSubscription.data?.keyword === "智能硬件产品" &&
      createdSubscription.data?.company === "小米" &&
      createdSubscription.data?.location === "北京",
    "关键词、公司和地点组合规则创建成功"
  );
  record(
    "P2 定向机会监控者",
    "接收新岗位通知",
    !subscriptionText.includes("通知能力列入下一阶段"),
    "页面仍明确说明通知能力属于下一阶段"
  );

  await page.screenshot({
    path: path.join(outputDir, "post-fix-p2-mobile-subscription.png"),
    fullPage: true,
  });
  await context.close();
}

async function runP3(browser) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  const request = context.request;
  await resetDemo(request);

  await page.goto(`${FRONTEND}/dashboard`);
  await page.getByText("投递轨迹", { exact: true }).waitFor();
  const dashboardBefore = await pageText(page);
  const kpiBefore = await apiJson(request, "/dashboard/kpi");
  const todoBefore = await apiJson(request, "/todo?days=14");
  record(
    "P3 复盘再投者",
    "查看投递数、进行中、漏斗和近期安排",
    kpiBefore.data?.total_applications === 5 &&
      kpiBefore.data?.pending_applications === 4 &&
      todoBefore.data?.length === 2 &&
      includesAll(dashboardBefore, ["投递记录", "进行中", "投递轨迹", "未来 14 天"]),
    "首页同时呈现全局数字、累计漏斗和近期动作"
  );

  await page.goto(`${FRONTEND}/applications`);
  await page.getByRole("tab", { name: "全部 5", exact: true }).waitFor();
  const applicationsText = await pageText(page);
  record(
    "P3 复盘再投者",
    "区分全部、进行中和已结束",
    includesAll(applicationsText, ["全部 5", "进行中 4", "已结束 1"]),
    "标准数据维持 5 / 4 / 1"
  );

  const tencentRow = page.locator("article").filter({ hasText: "腾讯 · 社交产品策划" });
  await tencentRow.waitFor();
  const tencentLink = tencentRow.getByRole("link", { name: "腾讯 · 社交产品策划", exact: true });
  const tencentHref = await tencentLink.getAttribute("href");
  const tencentApplicationId = Number(tencentHref?.split("/").at(-1));
  const statusSelect = tencentRow.locator("select");
  await waitForApi(
    page,
    `/applications/${tencentApplicationId}/transition`,
    () => statusSelect.selectOption("interviewing"),
    "POST"
  );
  record(
    "P3 复盘再投者",
    "从列表更新投递状态",
    (await tencentRow.innerText()).includes("面试中"),
    "列表更新后当前状态同步显示"
  );

  await tencentLink.click();
  await page.waitForURL(`**/applications/${tencentApplicationId}`);
  await page.waitForLoadState("networkidle");
  const events = await apiJson(request, `/applications/${tencentApplicationId}/events`);
  record(
    "P3 复盘再投者",
    "回看完整事件时间线",
    events.data?.some((event) => event.to_status === "applied") &&
      events.data?.some((event) => event.to_status === "interviewing"),
    "初始事件和刚完成的状态变化均可追溯"
  );

  await page.goto(`${FRONTEND}/dashboard`);
  const funnel = await apiJson(request, "/dashboard/funnel");
  const interviewStage = funnel.data?.funnel?.find((item) => item.status === "interviewing");
  await page.getByText("投递轨迹", { exact: true }).waitFor();
  const dashboardAfter = await pageText(page);
  record(
    "P3 复盘再投者",
    "验证状态变化进入累计漏斗",
    interviewStage?.count === 3 && dashboardAfter.includes("3 次到达"),
    "腾讯进入面试后，累计面试到达数由 2 增加为 3"
  );

  record(
    "P3 复盘再投者",
    "按公司、岗位方向或来源分析转化",
    includesAll(dashboardAfter, ["按公司", "岗位方向", "来源分析"]),
    "当前仍只有整体漏斗和最近更新"
  );

  await page.screenshot({
    path: path.join(outputDir, "post-fix-p3-dashboard.png"),
    fullPage: true,
  });
  await context.close();
}

async function runP4(browser) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  const request = context.request;
  await resetDemo(request);

  await page.goto(`${FRONTEND}/applications`);
  const beforeManual = await pageText(page);
  record(
    "P4 低维护意愿者",
    "从 Excel / Notion 批量导入历史投递",
    includesAll(beforeManual, ["Excel", "Notion", "导入历史投递"]),
    "当前没有历史导入入口"
  );

  const globalText = [
    beforeManual,
    await (async () => {
      await page.goto(`${FRONTEND}/dashboard`);
      return pageText(page);
    })(),
  ].join("\n");
  record(
    "P4 低维护意愿者",
    "从一封新通知自动建立投递",
    includesAll(globalText, ["新通知", "自动建立投递"]),
    "通知解析仍依赖已有投递详情"
  );

  await page.goto(`${FRONTEND}/applications`);
  await page.getByRole("button", { name: "补录外部投递", exact: true }).click();
  await page.getByPlaceholder("例如：Notion").fill("Linear");
  await page.getByPlaceholder("例如：Product Manager").fill("Product Manager, Core Experience");
  await page.getByPlaceholder("可选，例如：上海 / Remote").fill("Remote");
  await page.getByPlaceholder("https://...").fill("https://linear.app/careers/example");
  await page.getByPlaceholder("可选，例如投递渠道、联系人或简历版本").fill("官网投递，英文简历 v3");
  await waitForApi(
    page,
    "/applications/manual",
    () => page.getByRole("button", { name: "建立投递记录", exact: true }).click(),
    "POST"
  );
  await page.waitForURL(/\/applications\/\d+$/);
  const manualId = Number(page.url().split("/").at(-1));
  const manualApplication = await apiJson(request, `/applications/${manualId}`);
  const manualEvents = await apiJson(request, `/applications/${manualId}/events`);
  const manualText = await pageText(page);
  record(
    "P4 低维护意愿者",
    "手动补录岗位库之外的机会",
    manualApplication.data?.job?.source === "manual" &&
      manualEvents.data?.some((event) => event.to_status === "applied") &&
      includesAll(manualText, ["Linear", "Product Manager, Core Experience", "已投递"]),
    "最小字段一次提交创建手动岗位、正式投递和初始时间线"
  );

  await page.screenshot({
    path: path.join(outputDir, "post-fix-p4-manual-application.png"),
    fullPage: true,
  });
  await context.close();
}

const browser = await chromium.launch({ headless: true, channel: "chrome" });
try {
  await runP1(browser);
  await runP2(browser);
  await runP3(browser);
  await runP4(browser);
} finally {
  await browser.close();
}

const core = results.filter((item) => !item.role.startsWith("P4"));
const boundary = results.filter((item) => item.role.startsWith("P4"));
const summary = {
  date: new Date().toISOString(),
  environment: {
    frontend: FRONTEND,
    api: API,
    desktop_viewport: "1440x1000",
    mobile_viewport: "390x844",
    isolation: "每个角色开始前恢复标准演示数据",
  },
  core: {
    satisfied: core.filter((item) => item.result === "满足").length,
    total: core.length,
  },
  boundary: {
    satisfied: boundary.filter((item) => item.result === "满足").length,
    total: boundary.length,
  },
  all: {
    satisfied: results.filter((item) => item.result === "满足").length,
    total: results.length,
  },
  results,
};

console.log(JSON.stringify(summary, null, 2));
