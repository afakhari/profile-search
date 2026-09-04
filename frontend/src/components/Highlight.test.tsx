import {render,screen} from '@testing-library/react';
import {describe,expect,it} from 'vitest';
import {Highlight} from './Highlight';
describe('Highlight',()=>{it('renders custom markers as safe mark elements',()=>{const {container}=render(<Highlight text={'Uses [[H]]Python[[/H]] daily <script>alert(1)</script>'}/>);expect(screen.getByText('Python').tagName).toBe('MARK');expect(container.querySelector('script')).toBeNull();expect(container.textContent).toContain('<script>')})});
