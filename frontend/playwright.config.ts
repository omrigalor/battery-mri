import{defineConfig}from'@playwright/test';export default defineConfig({testDir:'.',testMatch:'smoke.spec.ts',timeout:140000,use:{headless:true},reporter:'list'});
