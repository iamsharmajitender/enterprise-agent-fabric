import type * as Preset from '@docusaurus/preset-classic';
import type {Config} from '@docusaurus/types';
import {themes as prismThemes} from 'prism-react-renderer';

const config: Config = {
  title: 'Enterprise Agent Fabric',
  tagline: 'One front door, many governed capabilities',
  favicon: 'img/favicon.svg',

  url: 'https://iamsharmajitender.github.io',
  baseUrl: '/enterprise-agent-fabric/',

  organizationName: 'iamsharmajitender',
  projectName: 'enterprise-agent-fabric',
  deploymentBranch: 'gh-pages',
  trailingSlash: false,

  onBrokenLinks: 'throw',
  onBrokenAnchors: 'throw',

  markdown: {
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'throw',
    },
  },
  themes: [
    '@docusaurus/theme-mermaid',
    [
      require.resolve('@easyops-cn/docusaurus-search-local'),
      {
        hashed: true,
        indexDocs: true,
        docsRouteBasePath: '/',
        explicitSearchResultPath: true,
      },
    ],
  ],

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          path: 'docs',
          routeBasePath: '/',
          sidebarPath: './sidebars.ts',
          showLastUpdateTime: true,
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Enterprise Agent Fabric',
      logo: {
        alt: 'Enterprise Agent Fabric',
        src: 'img/logo.svg',
      },
      items: [
        {to: '/guides', label: 'Guides', position: 'left'},
        {to: '/concepts/glossary', label: 'Concepts', position: 'left'},
        {to: '/architecture/the-idea', label: 'Architecture', position: 'left'},
        {to: '/reference', label: 'Reference', position: 'left'},
      ],
    },
    footer: {
      style: 'light',
      links: [
        {
          title: 'Concepts',
          items: [
            {label: 'Glossary', to: '/concepts/glossary'},
            {label: 'Authoring an agent', to: '/concepts/authoring-a-product/route'},
            {label: 'Executing a request', to: '/concepts/executing-a-request/request-lifecycle'},
          ],
        },
        {
          title: 'Architecture',
          items: [
            {label: 'The idea', to: '/architecture/the-idea'},
            {label: 'Operating model', to: '/architecture/operating-model'},
            {label: 'Technical design', to: '/architecture/technical-design'},
          ],
        },
        {
          title: 'Build and run',
          items: [
            {label: 'Start the fabric', to: '/running-locally'},
            {label: 'First request', to: '/guides/first-request'},
            {label: 'Reference', to: '/reference'},
          ],
        },
      ],
      copyright: 'Enterprise Agent Fabric documentation.',
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'json', 'sql', 'java', 'python', 'yaml'],
    },
    tableOfContents: {
      minHeadingLevel: 2,
      maxHeadingLevel: 4,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
