import React, { useState, useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import {
  MessageSquareText, MousePointerClick, RefreshCcw, Layout, Eye,
  Plus, Server, Play, StopCircle, HardDriveDownload
} from 'lucide-react';

// --- Mock Opcode Implementations ---

interface UIVectorElement {
  element_id: string;
  ui_element_vector: number[];
  bounding_box: { x: number; y: number; width: number; height: number; };
  element_type: 'button' | 'window' | 'text_input' | 'icon' | 'slider';
  semantic_description: string;
  state_color?: string; // For visual simulation
  text_content?: string;
  z_index: number;
  parent_id?: string; // To link elements to windows
}

interface ApplicationInstance {
  application_id: string;
  application_name: string;
  current_state_vector: number[];
  ui_elements_count: number;
  is_running: boolean;
}

let nextElementId = 1; // Simple ID generator for simulation
let nextAppId = 1; // Simple App ID generator

const generateVector = (description: string): number[] => {
  const base = description.length * 0.1;
  return Array.from({ length: 8 }, (_, i) => parseFloat((base + Math.random()).toFixed(4)));
};

const getBoundingBox = (x: number, y: number, width: number, height: number) => ({ x, y, width, height });

const mockGenerateUIElementVector = (
  element_type: UIVectorElement['element_type'],
  semantic_description: string,
  initial_state: { x: number; y: number; width: number; height: number; text_content?: string; color_hex?: string; z_index?: number; parent_id?: string; }
): UIVectorElement => {
  const element_id = `el_${nextElementId++}`;
  const ui_element_vector = generateVector(semantic_description);
  const bounding_box = getBoundingBox(initial_state.x, initial_state.y, initial_state.width, initial_state.height);
  return {
    element_id,
    ui_element_vector,
    bounding_box,
    element_type,
    semantic_description,
    state_color: initial_state.color_hex || '#60a5fa',
    text_content: initial_state.text_content,
    z_index: initial_state.z_index || 0,
    parent_id: initial_state.parent_id,
  };
};

const mockUpdateUIElementVectorState = (
  element: UIVectorElement,
  state_changes: any
): UIVectorElement => {
  const updatedElement = { ...element };
  updatedElement.ui_element_vector = generateVector(element.semantic_description + JSON.stringify(state_changes));

  if (state_changes.color_hex) { updatedElement.state_color = state_changes.color_hex; }
  if (state_changes.text_content !== undefined) updatedElement.text_content = state_changes.text_content;
  if (state_changes.x !== undefined) updatedElement.bounding_box.x = state_changes.x;
  if (state_changes.y !== undefined) updatedElement.bounding_box.y = state_changes.y;
  if (state_changes.width !== undefined) updatedElement.bounding_box.width = state_changes.width;
  if (state_changes.height !== undefined) updatedElement.bounding_box.height = state_changes.height;
  if (state_changes.z_index !== undefined) updatedElement.z_index = state_changes.z_index;

  return updatedElement;
};

const mockInterpretRawInputEvent = (
  raw_event_data: { device: string; action: string; coords?: [number, number]; key?: string }
) => {
  const input_event_vector = generateVector(JSON.stringify(raw_event_data));
  let event_type: 'click' | 'keydown' | 'keyup' | 'mousemove' | 'scroll' = 'click';
  let semantic_event_description = `Raw ${raw_event_data.device} ${raw_event_data.action}`;

  if (raw_event_data.action === 'click') event_type = 'click';
  return { input_event_vector, event_type, semantic_event_description };
};

const mockRouteInputEventVector = (
  input_event_vector: number[],
  current_viewport_elements_vectors: UIVectorElement[],
  event_coords?: [number, number]
) => {
  let target_element_id: string | null = null;
  let target_application_id: string | null = null; // Can be null if no app owns the element
  let semantic_action_trigger = 'no_action';

  if (event_coords) {
    const [clickX, clickY] = event_coords;
    const sortedElements = [...current_viewport_elements_vectors].sort((a, b) => b.z_index - a.z_index);

    for (const element of sortedElements) {
      const { x, y, width, height } = element.bounding_box;
      // Adjust click coordinates relative to parent if element has parent
      // For simplicity, we assume click coords are global and match element global position
      if (clickX >= x && clickX <= x + width && clickY >= y && clickY <= y + height) {
        target_element_id = element.element_id;
        semantic_action_trigger = `${element.element_type}_clicked`;
        // In a real system, we'd map element to its owning application
        if (element.parent_id) {
          // Mock logic: assuming parent_id implies app ownership for this simulation
          target_application_id = `app_${element.parent_id.split('_')[1] || 'default'}`;
        } else {
          // If no parent, it could be a desktop element or system element
          target_application_id = 'VectorOS_Desktop';
        }
        break;
      }
    }
  }
  return { target_element_id, target_application_id, semantic_action_trigger };
};

const mockSynthesizeViewportVector = (all_active_ui_element_vectors: UIVectorElement[], viewport_dimensions: { width: number, height: number }) => {
  const sortedElements = [...all_active_ui_element_vectors].sort((a, b) => a.z_index - b.z_index);
  const combinedVectors = sortedElements.flatMap(e => e.ui_element_vector);
  const viewport_vector = generateVector(`viewport_${viewport_dimensions.width}x${viewport_dimensions.height}_${combinedVectors.join(',')}`);
  const semantic_viewport_description = `Viewport showing ${all_active_ui_element_vectors.length} elements.`;
  return { viewport_vector, semantic_viewport_description };
};

const mockTranslateViewportToRenderCommands = (viewport_vector: number[], target_graphics_api: string, display_resolution: { width: number, height: number }) => {
  const commands = [`INIT_GRAPHICS_CONTEXT('${target_graphics_api}', ${display_resolution.width}, ${display_resolution.height})`];
  commands.push(`DRAW_BACKGROUND(0xCCCCCC)`);
  commands.push(`RENDER_VECTOR_STATE(${viewport_vector.slice(0, 4).join(',')})`);
  commands.push(`FLUSH_FRAME`);
  return { render_commands_sequence: commands, estimated_render_time_ms: 16 };
};

const mockDisplayPixelBuffer = (render_commands_sequence: string[]) => {
  return { display_success: true, frame_rate_achieved_fps: 60 };
};

// Application Management Opcodes (Conceptual Mocks)
const mockLaunchApplicationWorkflow = (application_name: string, initial_parameters: any = {}) => {
  const application_id = `app_${nextAppId++}`;
  const appStateDescription = `${application_name} instance ${application_id} with params ${JSON.stringify(initial_parameters)}`;
  const application_state_vector = generateVector(appStateDescription);
  return { application_id, application_name, current_state_vector: application_state_vector, ui_elements_count: 0, is_running: true };
};

const mockTerminateApplicationWorkflow = (app: ApplicationInstance) => {
  return { terminated_successfully: true, final_state_persisted: true };
};

const mockGetActiveApplicationsVectors = (activeApps: ApplicationInstance[], query_filter?: string) => {
  let filteredApps = activeApps;
  if (query_filter) {
    filteredApps = activeApps.filter(app => app.application_name.toLowerCase().includes(query_filter.toLowerCase()));
  }
  return { active_applications: filteredApps };
};


// --- React Component ---

export default function VectorOSSimulator() {
  const [uiElements, setUiElements] = useState<UIVectorElement[]>([]);
  const [activeApplications, setActiveApplications] = useState<ApplicationInstance[]>([]);
  const [log, setLog] = useState<string[]>([]);
  const [elementX, setElementX] = useState<number>(50);
  const [elementY, setElementY] = useState<number>(50);
  const [elementZ, setElementZ] = useState<number>(0);
  const [elementColor, setElementColor] = useState<string>('#60a5fa');
  const [elementText, setElementText] = useState<string>('Click Me');
  const [elementType, setElementType] = useState<UIVectorElement['element_type']>('button');
  const [kernelEventCount, setKernelEventCount] = useState<number>(0);
  const [appToLaunch, setAppToLaunch] = useState<string>('VectorApp');
  const viewportDimensions = useMemo(() => ({ width: 400, height: 300 }), []);

  const addLog = useCallback((message: string) => {
    setLog(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`].slice(-10));
    setKernelEventCount(prev => prev + 1);
  }, []);

  const handleGenerateElement = useCallback(() => {
    const newElement = mockGenerateUIElementVector(
      elementType,
      `A ${elementType} with text '${elementText}' at (${elementX},${elementY})`,
      { x: elementX, y: elementY, width: elementType === 'button' ? 100 : 200, height: elementType === 'button' ? 40 : 150, text_content: elementText, color_hex: elementColor, z_index: elementZ }
    );
    setUiElements(prev => [...prev, newElement]);
    addLog(`GENERATE_UI_ELEMENT_VECTOR: Created ${elementType} '${newElement.element_id}' at (${newElement.bounding_box.x}, ${newElement.bounding_box.y}) with Z: ${newElement.z_index}`);
  }, [addLog, elementX, elementY, elementZ, elementColor, elementText, elementType]);


  const handleSimulateClick = useCallback((clickX: number, clickY: number) => {
    if (uiElements.length === 0) {
      addLog("No elements to click. Generate one first!");
      return;
    }

    addLog(`Simulating raw input: mouse click at (${clickX}, ${clickY})`);
    const { input_event_vector, event_type, semantic_event_description } = mockInterpretRawInputEvent({
      device: 'mouse',
      action: 'click',
      coords: [clickX, clickY],
    });
    addLog(`INTERPRET_RAW_INPUT_EVENT: Type '${event_type}', Desc: '${semantic_event_description}'`);

    const { target_element_id, target_application_id, semantic_action_trigger } = mockRouteInputEventVector(
      input_event_vector,
      uiElements,
      [clickX, clickY]
    );

    if (target_element_id) {
      addLog(`ROUTE_INPUT_EVENT_VECTOR: Click routed to element '${target_element_id}' (App: ${target_application_id}). Trigger: '${semantic_action_trigger}'`);
      // Simulate element action (e.g., change its color temporarily)
      setUiElements(prev => prev.map(el => {
        if (el.element_id === target_element_id) {
          const clickedElement = mockUpdateUIElementVectorState(el, { color_hex: '#ef4444' }); // Red on click
          addLog(`Simulated: Element '${el.element_id}' state changed (color red).`);
          setTimeout(() => {
            setUiElements(current => current.map(currEl =>
              currEl.element_id === target_element_id ? mockUpdateUIElementVectorState(clickedElement, { color_hex: el.state_color }) : currEl
            ));
            addLog(`Simulated: Element color reverted.`);
          }, 500);
          return clickedElement;
        }
        return el;
      }));

      // If it's a window, bring it to front (increase Z-index)
      setUiElements(prev => prev.map(el => {
        if (el.element_id === target_element_id && el.element_type === 'window') {
          const maxZ = Math.max(...prev.map(e => e.z_index));
          return mockUpdateUIElementVectorState(el, { z_index: maxZ + 1 });
        }
        return el;
      }));

    } else {
      addLog(`ROUTE_INPUT_EVENT_VECTOR: Click not routed to any element. Target: ${target_element_id || 'None'}`);
    }
  }, [uiElements, addLog, elementColor, elementText, elementX, elementY, elementZ]);

  const handleRenderViewport = useCallback(() => {
    if (uiElements.length === 0) {
      addLog("Nothing to render. Generate UI elements first!");
      return;
    }

    addLog(`SYNTHESIZE_VIEWPORT_VECTOR: Composing ${uiElements.length} elements into viewport vector...`);
    const { viewport_vector, semantic_viewport_description } = mockSynthesizeViewportVector(
      uiElements,
      viewportDimensions
    );
    addLog(`Result: ${semantic_viewport_description}, Vector: [${viewport_vector.slice(0, 3).join(', ')}...]`);

    addLog(`TRANSLATE_VIEWPORT_TO_RENDER_COMMANDS: Converting viewport vector to display commands...`);
    const { render_commands_sequence, estimated_render_time_ms } = mockTranslateViewportToRenderCommands(
      viewport_vector,
      'WebGPU',
      viewportDimensions
    );
    addLog(`Result: ${render_commands_sequence.length} commands, Est. Time: ${estimated_render_time_ms}ms.`);

    addLog(`DISPLAY_PIXEL_BUFFER: Sending commands to display hardware...`);
    const { display_success, frame_rate_achieved_fps } = mockDisplayPixelBuffer(render_commands_sequence);
    addLog(`Result: Display success: ${display_success}, Achieved FPS: ${frame_rate_achieved_fps}.`);
  }, [uiElements, addLog, viewportDimensions]);

  const handleLaunchApp = useCallback(() => {
    const newApp = mockLaunchApplicationWorkflow(appToLaunch, { display_width: 200, display_height: 150 });
    setActiveApplications(prev => [...prev, newApp]);
    addLog(`LAUNCH_APPLICATION_WORKFLOW: Launched app '${newApp.application_name}' with ID '${newApp.application_id}'.`);

    // Simulate an app creating its own window
    const appWindow = mockGenerateUIElementVector(
      'window',
      `${newApp.application_name} Window`,
      { x: Math.random() * (viewportDimensions.width - 250), y: Math.random() * (viewportDimensions.height - 200), width: 250, height: 200, text_content: newApp.application_name, color_hex: '#3366ff', z_index: activeApplications.length + 1, parent_id: newApp.application_id }
    );
    setUiElements(prev => [...prev, appWindow]);
    addLog(`GENERATE_UI_ELEMENT_VECTOR: App '${newApp.application_id}' created window '${appWindow.element_id}'.`);
  }, [addLog, appToLaunch, activeApplications.length, viewportDimensions]);

  const handleTerminateApp = useCallback((appId: string) => {
    const appToTerminate = activeApplications.find(app => app.application_id === appId);
    if (!appToTerminate) return;

    const { terminated_successfully } = mockTerminateApplicationWorkflow(appToTerminate);
    if (terminated_successfully) {
      setActiveApplications(prev => prev.filter(app => app.application_id !== appId));
      setUiElements(prev => prev.filter(el => el.parent_id !== appId)); // Remove app's UI elements
      addLog(`TERMINATE_APPLICATION_WORKFLOW: Terminated app '${appToTerminate.application_name}' (ID: ${appId}).`);
    } else {
      addLog(`TERMINATE_APPLICATION_WORKFLOW: Failed to terminate app '${appToTerminate.application_name}' (ID: ${appId}).`);
    }
  }, [addLog, activeApplications]);

  const handleGetActiveApps = useCallback(() => {
    const { active_applications } = mockGetActiveApplicationsVectors(activeApplications);
    addLog(`GET_ACTIVE_APPLICATIONS_VECTORS: Found ${active_applications.length} active apps.`);
    active_applications.forEach(app => addLog(`  - App ID: ${app.application_id}, Name: ${app.application_name}`));
  }, [addLog, activeApplications]);


  return (
    <div className="p-8 space-y-8 bg-gray-50 dark:bg-gray-900 min-h-screen font-sans">
      <h1 className="text-4xl font-extrabold text-center text-gray-800 dark:text-gray-100 mb-8 tracking-tight">
        VectorOS GUI Simulator
      </h1>
      <p className="text-center text-gray-600 dark:text-gray-300 max-w-2xl mx-auto mb-10">
        This simulation demonstrates the conceptual flow of Opcodes in a Vector-Native GUI Operating System.
        Generate UI elements, launch/terminate applications, simulate user input, and observe the rendering pipeline.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
        {/* Element Creator */}
        <Card className="col-span-1 shadow-lg border-none">
          <CardHeader className="bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-t-lg">
            <CardTitle className="flex items-center text-lg"><Plus className="mr-2 h-5 w-5" />Element Creator</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 p-6">
            <div>
              <Label htmlFor="elementType" className="text-sm font-medium">Element Type</Label>
              <select id="elementType" value={elementType} onChange={(e) => setElementType(e.target.value as UIVectorElement['element_type'])}
                className="w-full mt-1 p-2 border rounded-md dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600">
                <option value="button">Button</option>
                <option value="window">Window</option>
              </select>
            </div>
            <div>
              <Label htmlFor="elementText" className="text-sm font-medium">Element Text</Label>
              <Input id="elementText" value={elementText} onChange={(e) => setElementText(e.target.value)} placeholder="Enter element text" className="mt-1" />
            </div>
            <div>
              <Label htmlFor="elementColor" className="text-sm font-medium">Element Color</Label>
              <Input id="elementColor" type="color" value={elementColor} onChange={(e) => setElementColor(e.target.value)} className="w-full h-10 p-1 mt-1 border-none rounded-md" />
            </div>
            <div>
              <Label htmlFor="elementX" className="text-sm font-medium">X Position</Label>
              <Slider id="elementX" min={0} max={viewportDimensions.width - 100} step={1} value={[elementX]} onValueChange={(val) => setElementX(val[0])} className="mt-2" />
              <span className="text-sm text-gray-600 dark:text-gray-400">X: {elementX}px</span>
            </div>
            <div>
              <Label htmlFor="elementY" className="text-sm font-medium">Y Position</Label>
              <Slider id="elementY" min={0} max={viewportDimensions.height - 40} step={1} value={[elementY]} onValueChange={(val) => setElementY(val[0])} className="mt-2" />
              <span className="text-sm text-gray-600 dark:text-gray-400">Y: {elementY}px</span>
            </div>
            <div>
              <Label htmlFor="elementZ" className="text-sm font-medium">Z-Index (Stacking Order)</Label>
              <Slider id="elementZ" min={0} max={10} step={1} value={[elementZ]} onValueChange={(val) => setElementZ(val[0])} className="mt-2" />
              <span className="text-sm text-gray-600 dark:text-gray-400">Z: {elementZ}</span>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-3 p-6 pt-0">
            <Button onClick={handleGenerateElement} className="w-full bg-green-600 hover:bg-green-700 text-white">
              <MessageSquareText className="mr-2 h-4 w-4" /> GENERATE_UI_ELEMENT_VECTOR
            </Button>
          </CardFooter>
        </Card>

        {/* Application Manager */}
        <Card className="col-span-1 shadow-lg border-none">
          <CardHeader className="bg-gradient-to-r from-yellow-500 to-orange-600 text-white rounded-t-lg">
            <CardTitle className="flex items-center text-lg"><Server className="mr-2 h-5 w-5" />Application Manager</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 p-6">
            <div>
              <Label htmlFor="appToLaunch" className="text-sm font-medium">Application Name</Label>
              <Input id="appToLaunch" value={appToLaunch} onChange={(e) => setAppToLaunch(e.target.value)} placeholder="e.g., VectorBrowser" className="mt-1" />
            </div>
            <Button onClick={handleLaunchApp} className="w-full bg-blue-600 hover:bg-blue-700 text-white">
              <Play className="mr-2 h-4 w-4" /> LAUNCH_APPLICATION_WORKFLOW
            </Button>
            <Button onClick={handleGetActiveApps} className="w-full" variant="secondary">
              <HardDriveDownload className="mr-2 h-4 w-4" /> GET_ACTIVE_APPLICATIONS_VECTORS
            </Button>
            <div className="mt-4 space-y-2">
              <h3 className="text-md font-semibold text-gray-800 dark:text-gray-100">Active Applications:</h3>
              {activeApplications.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">No applications running.</p>
              ) : (
                activeApplications.map(app => (
                  <div key={app.application_id} className="flex items-center justify-between bg-gray-100 dark:bg-gray-700 p-2 rounded-md">
                    <span className="text-sm text-gray-800 dark:text-gray-100">{app.application_name} ({app.application_id})</span>
                    <Button variant="destructive" size="sm" onClick={() => handleTerminateApp(app.application_id)}>
                      <StopCircle className="h-3 w-3 mr-1" /> Terminate
                    </Button>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Viewport Simulation */}
        <Card className="col-span-1 shadow-lg border-none">
          <CardHeader className="bg-gradient-to-r from-purple-600 to-pink-500 text-white rounded-t-lg">
            <CardTitle className="flex items-center text-lg"><Layout className="mr-2 h-5 w-5" />VectorOS Viewport</CardTitle>
          </CardHeader>
          <CardContent
            className="flex-grow relative border-2 border-dashed border-gray-300 dark:border-gray-700 bg-gray-100 dark:bg-gray-800 rounded-b-md overflow-hidden p-0"
            style={{ width: viewportDimensions.width, height: viewportDimensions.height }}
            onClick={(e) => handleSimulateClick(e.nativeEvent.offsetX, e.nativeEvent.offsetY)}
          >
            {uiElements.sort((a,b) => a.z_index - b.z_index).map((element) => (
              <div
                key={element.element_id}
                style={{
                  position: 'absolute',
                  left: element.bounding_box.x,
                  top: element.bounding_box.y,
                  width: element.bounding_box.width,
                  height: element.bounding_box.height,
                  backgroundColor: element.element_type === 'window' ? '#f0f0f0' : element.state_color, // Different styling for windows
                  border: element.element_type === 'window' ? '2px solid #3366ff' : 'none',
                  borderRadius: element.element_type === 'window' ? '8px' : '4px',
                  boxShadow: element.element_type === 'window' ? '0 4px 8px rgba(0,0,0,0.2)' : 'none',
                  zIndex: element.z_index,
                  display: 'flex',
                  alignItems: element.element_type === 'window' ? 'flex-start' : 'center',
                  justifyContent: element.element_type === 'window' ? 'flex-start' : 'center',
                  padding: element.element_type === 'window' ? '5px' : '0',
                  color: element.element_type === 'window' ? '#333' : 'white',
                  cursor: 'pointer',
                }}
                className="transition-all duration-100 ease-in-out text-white overflow-hidden"
              >
                {element.element_type === 'window' && (
                  <div className="w-full bg-blue-700 text-white p-1 text-xs font-bold rounded-t-md -mx-1 -mt-1 mb-1 flex justify-between items-center">
                    {element.text_content}
                    <span className="text-xs opacity-70">({element.element_id})</span>
                  </div>
                )}
                {element.element_type !== 'window' && element.text_content}
                <span className="absolute bottom-0 right-1 text-xs opacity-50 bg-black bg-opacity-30 rounded px-1">Z:{element.z_index}</span>
              </div>
            ))}
          </CardContent>
          <CardFooter className="flex flex-col space-y-3 p-6">
            <Button onClick={() => handleSimulateClick(viewportDimensions.width / 2, viewportDimensions.height / 2)} className="w-full bg-orange-500 hover:bg-orange-600 text-white" disabled={uiElements.length === 0}>
              <MousePointerClick className="mr-2 h-4 w-4" /> Simulate Click (Viewport)
            </Button>
            <Button onClick={handleRenderViewport} className="w-full bg-blue-600 hover:bg-blue-700 text-white" disabled={uiElements.length === 0}>
              <Eye className="mr-2 h-4 w-4" /> SYNTHESIZE & TRANSLATE & DISPLAY
            </Button>
          </CardFooter>
        </Card>

        {/* Simulation Log */}
        <Card className="col-span-1 shadow-lg border-none">
          <CardHeader className="bg-gradient-to-r from-pink-500 to-red-600 text-white rounded-t-lg">
            <CardTitle className="flex items-center text-lg"><MessageSquareText className="mr-2 h-5 w-5" />Vector Kernel Log & Status</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col h-[400px]">
            <div className="mb-4 p-3 bg-gray-100 dark:bg-gray-800 rounded-md">
              <p className="text-sm text-gray-800 dark:text-gray-100">
                Active UI Elements: <span className="font-bold text-blue-500">{uiElements.length}</span>
              </p>
              <p className="text-sm text-gray-800 dark:text-gray-100">
                Kernel Events Processed: <span className="font-bold text-purple-500">{kernelEventCount}</span>
              </p>
            </div>
            <div className="flex-grow overflow-y-auto text-sm bg-gray-800 text-gray-200 rounded-md p-2">
              {log.length === 0 ? (
                <p className="text-gray-400">No events yet. Generate a UI element or launch an app!</p>
              ) : (
                log.map((entry, index) => (
                  <p key={index} className="mb-1 last:mb-0 border-b border-gray-700 last:border-0 pb-1">
                    {entry}
                  </p>
                ))
              )}
            </div>
          </CardContent>
          <CardFooter className="p-6 pt-0">
            <Button onClick={() => setLog([])} variant="ghost" className="w-full text-red-500 hover:bg-red-900/10">Clear Log</Button>
          </CardFooter>
        </Card>
      </div>

      {/* Debug/Vector Display for all elements */}
      {uiElements.length > 0 && (
        <Card className="shadow-lg border-none">
          <CardHeader className="bg-gray-700 text-white rounded-t-lg">
            <CardTitle className="text-lg">All Active UI Element Vectors & States</CardTitle>
          </CardHeader>
          <CardContent className="text-sm font-mono bg-gray-100 dark:bg-gray-800 p-4 rounded-b-md overflow-x-auto max-h-96">
            {uiElements.map((element, index) => (
              <div key={element.element_id} className={`pb-4 mb-4 ${index < uiElements.length - 1 ? 'border-b border-gray-300 dark:border-gray-700' : ''}`}>
                <pre className="whitespace-pre-wrap break-all">
                  {JSON.stringify({
                    element_id: element.element_id,
                    element_type: element.element_type,
                    semantic_description: element.semantic_description,
                    ui_element_vector: element.ui_element_vector,
                    bounding_box: element.bounding_box,
                    state_color: element.state_color,
                    text_content: element.text_content,
                    z_index: element.z_index,
                    parent_id: element.parent_id,
                  }, null, 2)}
                </pre>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Debug/Vector Display for Active Applications */}
      {activeApplications.length > 0 && (
        <Card className="shadow-lg border-none">
          <CardHeader className="bg-gray-700 text-white rounded-t-lg">
            <CardTitle className="text-lg">Active Application Vectors & States</CardTitle>
          </CardHeader>
          <CardContent className="text-sm font-mono bg-gray-100 dark:bg-gray-800 p-4 rounded-b-md overflow-x-auto max-h-96">
            {activeApplications.map((app, index) => (
              <div key={app.application_id} className={`pb-4 mb-4 ${index < activeApplications.length - 1 ? 'border-b border-gray-300 dark:border-gray-700' : ''}`}>
                <pre className="whitespace-pre-wrap break-all">
                  {JSON.stringify({
                    application_id: app.application_id,
                    application_name: app.application_name,
                    is_running: app.is_running,
                    current_state_vector: app.current_state_vector,
                  }, null, 2)}
                </pre>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
