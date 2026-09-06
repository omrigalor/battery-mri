// DOM/behavior coverage; Plotly is mocked. This does not claim browser rendering acceptance.
import React from 'react';
import{describe,it,expect,vi,afterEach}from'vitest';
import{render,screen,fireEvent,act,cleanup}from'@testing-library/react';
import fs from'node:fs';import App from'./App';
vi.mock('plotly.js-basic-dist-min',()=>({default:{react:vi.fn((_el,traces)=>{for(const t of traces){for(const v of [...(t.x||[]),...(t.y||[])]){if(!Number.isFinite(v))throw Error('Nonfinite chart value')}}}),purge:vi.fn(),Plots:{resize:vi.fn()}}}));
const data=JSON.parse(fs.readFileSync('../backend/data/demo.json','utf8'));
vi.stubGlobal('ResizeObserver',class{observe(){}disconnect(){}});
afterEach(()=>{cleanup();vi.useRealTimers()});
async function load(){vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>data})));render(<App/>);await act(async()=>{await Promise.resolve()});}
describe('guided presentation',()=>{
 it('starts, pauses, resumes, advances, and completes automatically',async()=>{
  vi.useFakeTimers();await load();fireEvent.click(screen.getByRole('button',{name:/Start demo/}));
  expect(screen.getByRole('heading',{name:'One cell. Two explanations.'})).toBeTruthy();
  fireEvent.click(screen.getByRole('button',{name:'Pause',exact:true}));act(()=>{vi.advanceTimersByTime(12000)});
  expect(screen.getByRole('heading',{name:'One cell. Two explanations.'})).toBeTruthy();
  fireEvent.click(screen.getByRole('button',{name:'Resume',exact:true}));
  for(let i=0;i<85;i++)act(()=>{vi.advanceTimersByTime(1000)});
  expect(screen.getByRole('heading',{name:'From passive analysis to active interrogation.'})).toBeTruthy();
  expect(screen.getAllByText('99.3%').length).toBeGreaterThan(0);
  fireEvent.click(screen.getByRole('button',{name:'Replay',exact:true}));expect(screen.getByRole('heading',{name:'One cell. Two explanations.'})).toBeTruthy();
 });
 it('supports next, skip, captions and technical drawers',async()=>{
  await load();fireEvent.click(screen.getByRole('button',{name:/Start demo/}));
  fireEvent.click(screen.getByRole('button',{name:'Next',exact:true}));expect(screen.getByRole('heading',{name:'An ordinary test leaves ambiguity.'})).toBeTruthy();
  fireEvent.click(screen.getByRole('button',{name:'Subtitles on'}));expect(screen.getByRole('button',{name:'Subtitles off'})).toBeTruthy();
  fireEvent.click(screen.getByRole('button',{name:'Show the math'}));expect(screen.getByRole('dialog')).toBeTruthy();fireEvent.click(screen.getByRole('button',{name:'Close ✕'}));
  fireEvent.click(screen.getByRole('button',{name:'Skip to result'}));expect(screen.getByRole('button',{name:'Reveal ground truth'})).toBeTruthy();
 });
});
