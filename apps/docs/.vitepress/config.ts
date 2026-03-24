import { defineConfig } from 'vitepress'

export default defineConfig({
  base: '/docs/',
  title: 'SkillHub Docs',
  description: 'User documentation for the SkillHub AI Skills Marketplace',

  themeConfig: {
    logo: '/logo.svg',

    nav: [
      { text: 'Back to SkillHub', link: process.env.SKILLHUB_APP_URL ?? 'http://localhost:5173' },
    ],

    sidebar: [
      {
        text: 'Guide',
        items: [
          { text: 'Getting Started', link: '/getting-started' },
          { text: 'Introduction to Skills', link: '/introduction-to-skills' },
          { text: 'Uses for Skills', link: '/uses-for-skills' },
          { text: 'Skill Discovery', link: '/skill-discovery' },
          { text: 'Social Features', link: '/social-features' },
          { text: 'Advanced Usage', link: '/advanced-usage' },
        ],
      },
      {
        text: 'Contributing',
        items: [
          { text: 'Submitting a Skill', link: '/submitting-a-skill' },
          { text: 'Feature Requests', link: '/feature-requests' },
        ],
      },
      {
        text: 'Reference',
        items: [
          { text: 'FAQ', link: '/faq' },
          { text: 'Resources', link: '/resources' },
        ],
      },
      {
        text: 'Administration',
        items: [
          { text: 'Admin Guide', link: '/admin-guide' },
        ],
      },
    ],
  },
})
