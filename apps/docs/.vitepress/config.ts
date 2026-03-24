import { defineConfig } from 'vitepress'

export default defineConfig({
  base: '/docs/',
  title: 'SkillHub Docs',
  description: 'User documentation for the SkillHub AI Skills Marketplace',
  appearance: 'dark',

  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/docs/logo.svg' }],
  ],

  themeConfig: {
    siteTitle: 'SkillHub Docs',

    nav: [
      { text: 'Guide', link: '/getting-started' },
      { text: 'Contributing', link: '/submitting-a-skill' },
      { text: 'Back to SkillHub', link: 'http://localhost:5173/' },
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

    outline: {
      level: [2, 3],
      label: 'On this page',
    },

    search: {
      provider: 'local',
    },
  },
})
