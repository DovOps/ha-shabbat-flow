const config = {
  title: 'Shabbat Flow',
  tagline: 'A peaceful Shabbat starts with a plan.',
  url: 'https://dovops.io',
  baseUrl: '/ha-shabbat-flow/',
  organizationName: 'DovOps', projectName: 'ha-shabbat-flow', trailingSlash: true,
  favicon: 'img/favicon.svg',
  onBrokenLinks: 'throw',
  markdown: {format: 'md', hooks: {onBrokenMarkdownLinks: 'throw'}},
  i18n: {defaultLocale: 'en', locales: ['en','he'], localeConfigs: {en: {label:'English'}, he: {label:'עברית',direction:'rtl',htmlLang:'he'}}},
  presets: [['classic', {docs: {numberPrefixParser:false,path:'generated/docs',routeBasePath:'docs',sidebarPath:require.resolve('./sidebars.js')}, blog:false, theme:{customCss:require.resolve('./src/css/custom.css')}}]],
  themeConfig: {
    colorMode: {defaultMode:'light',disableSwitch:true},
    navbar: {title:'',logo:{alt:'ShabbatFlow',src:'img/logo.png'},items:[
      {to:'/docs/start',label:'Get started',position:'right'},
      {to:'/docs/adoption',label:'Adoption playbook',position:'right'},
      {to:'/gallery',label:'Gallery',position:'right'},
      {to:'/docs/contributing',label:'Developer guide',position:'right'},
      {to:'/docs/specifications',label:'Specifications',position:'right'},
      {href:'https://github.com/DovOps/ha-shabbat-flow',label:'GitHub',position:'right'},
      {type:'localeDropdown',position:'right'}]},
    footer:{style:'dark',links:[{title:'Explore',items:[{label:'Get started',to:'/docs/start'},{label:'Capabilities & roadmap',to:'/docs/capabilities'},{label:'Specifications',to:'/docs/specifications'}]},{title:'Build together',items:[{label:'Developer guide',to:'/docs/contributing'},{label:'Source on GitHub',href:'https://github.com/DovOps/ha-shabbat-flow'}]}],copyright:'ShabbatFlow · An independent Home Assistant custom integration.'}
  }
};
module.exports=config;
