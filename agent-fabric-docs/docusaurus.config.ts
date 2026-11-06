import type * as Preset from '@docusaurus/preset-classic';
import type {Config} from '@docusaurus/types';
import {themes as prismThemes} from 'prism-react-renderer';

const config: Config = {
  title: 'Enterprise Agent Fabric',
  tagline: 'An operating model for enterprise agents',
  favicon: 'img/favicon.svg',

  url: 'https://eaf.jitendersharma.dev',
  baseUrl: '/',

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
        {to: '/how-it-hangs-together', label: 'How it works', position: 'left'},
        {to: '/architecture/the-idea', label: 'Architecture', position: 'left'},
        {to: '/autonomy/', label: 'Autonomy', position: 'left'},
        {to: '/use-cases/', label: 'Use cases', position: 'left'},
      ],
    },
    footer: {
      style: 'light',
      links: [
        {
          title: 'The story',
          items: [
            {label: 'How it hangs together', to: '/how-it-hangs-together'},
            {label: 'The idea', to: '/architecture/the-idea'},
            {label: 'Operating model', to: '/architecture/operating-model'},
          ],
        },
        {
          title: 'Go deeper',
          items: [
            {label: 'Request lifecycle', to: '/concepts/executing-a-request/request-lifecycle'},
            {label: 'Identities', to: '/concepts/executing-a-request/identities'},
            {label: 'Autonomy', to: '/autonomy/'},
            {label: 'Use cases', to: '/use-cases/'},
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
