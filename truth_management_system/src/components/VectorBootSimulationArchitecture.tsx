import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  ArrowRight,
  Power,
  Cpu,
  Disc,
  MemoryStick,
  Server,
  Workflow, // Icon for orchestrator/workflow
  ArrowDown, // For hierarchical connection
  Terminal, // For shell/init system
  Network,
  Settings, // For general configuration
} from 'lucide-react';

// Define the structure for an atomic opcode for display
interface DisplayAtomicOpcode {
  name: string;
  description: string; // Simplified for display
}

// Define the structure for a workflow stage within the orchestrator
interface DisplayWorkflowStage {
  title: string;
  description: string;
  icon: React.ElementType;
  workflowOpcodeName: string; // The name of the workflow Opcode
  atomicOpcodes: DisplayAtomicOpcode[];
}

// Define the overall orchestrator structure
interface VectorBootOrchestrator {
  title: string;
  description: string;
  orchestratorOpcodeName: string;
  stages: DisplayWorkflowStage[];
}

const vectorBootOrchestrator: VectorBootOrchestrator = {
  title: "VectorBoot: x86-like Linux OS Boot Simulation",
  description: "An orchestrated simulation of a Linux OS boot process in the Vector Universe, from power-on to user-space readiness, utilizing a hierarchy of Opcodes.",
  orchestratorOpcodeName: "VECTOR_KERNEL_ORCHESTRATOR",
  stages: [
    {
      title: "Stage 0-1: BIOS/UEFI Boot Workflow",
      description: "Handles initial power-on, hardware self-test, device initialization, and boot device selection.",
      icon: Power,
      workflowOpcodeName: "BIOS_UEFI_BOOT_WORKFLOW",
      atomicOpcodes: [
        { name: "POWER_ON_VECTOR_TRIGGER", description: "Initiates power-on state." },
        { name: "PERFORM_POWER_ON_SELF_TEST_OPCODE", description: "Checks hardware integrity." },
        { name: "INITIALIZE_HARDWARE_OPCODE", description: "Configures detected hardware." },
        { name: "SELECT_BOOT_DEVICE_OPCODE", description: "Identifies primary boot device." },
        { name: "LOAD_BOOT_SECTOR_OPCODE", description: "Reads bootloader code." },
      ],
    },
    {
      title: "Stage 2: Bootloader Workflow",
      description: "Executes the boot sector, loads bootloader config, and prepares kernel/initramfs.",
      icon: Disc,
      workflowOpcodeName: "BOOTLOADER_WORKFLOW",
      atomicOpcodes: [
        { name: "EXECUTE_BOOT_SECTOR_CODE_OPCODE", description: "Runs bootloader's first stage." },
        { name: "LOAD_BOOTLOADER_CONFIG_OPCODE", description: "Parses bootloader configuration." },
        { name: "LOAD_KERNEL_IMAGE_OPCODE", description: "Loads kernel and initramfs." },
      ],
    },
    {
      title: "Stage 3: Kernel Initialization Workflow",
      description: "Decompresses kernel, initializes CPU/memory, loads virtual drivers, and mounts root filesystem.",
      icon: Cpu, // Changed to CPU as kernel is CPU-centric
      workflowOpcodeName: "KERNEL_INIT_WORKFLOW",
      atomicOpcodes: [
        { name: "DECOMPRESS_KERNEL_OPCODE", description: "Unpacks compressed kernel." },
        { name: "INITIALIZE_CPU_MEMORY_OPCODE", description: "Sets up CPU and memory for kernel." },
        { name: "LOAD_VIRTUAL_DRIVERS_OPCODE", description: "Initializes virtual hardware drivers." },
        { name: "MOUNT_ROOT_FILESYSTEM_OPCODE", description: "Mounts the root file system." },
      ],
    },
    {
      title: "Stage 4: Init System Workflow",
      description: "Launches PID 1, reads service configurations, starts services, and sets up networking.",
      icon: Terminal, // Using Terminal to represent the user-space init process
      workflowOpcodeName: "INIT_SYSTEM_WORKFLOW",
      atomicOpcodes: [
        { name: "LAUNCH_PID1_OPCODE", description: "Starts the initial user-space process." },
        { name: "READ_SERVICE_CONFIG_OPCODE", description: "Builds service dependency graph." },
        { name: "START_SERVICE_OPCODE", description: "Launches individual services." },
        { name: "SETUP_NETWORK_OPCODE", description: "Configures network interfaces." },
      ],
    },
  ],
};

export default function VectorBootSimulationArchitecture() {
  return (
    <div className="container mx-auto p-6 space-y-10">
      <Card className="p-8 shadow-lg bg-gradient-to-br from-blue-50 to-indigo-100">
        <CardHeader className="text-center">
          <Workflow className="mx-auto h-12 w-12 text-blue-600 mb-4" />
          <CardTitle className="text-5xl font-extrabold text-blue-800 tracking-tight">
            {vectorBootOrchestrator.title}
          </CardTitle>
          <p className="mt-4 text-xl text-blue-700 font-medium max-w-3xl mx-auto">
            {vectorBootOrchestrator.description}
          </p>
          <Badge className="mt-4 text-lg px-4 py-2 bg-blue-600 text-white hover:bg-blue-700">
            Orchestrator: {vectorBootOrchestrator.orchestratorOpcodeName}
          </Badge>
        </CardHeader>
      </Card>

      <h2 className="text-3xl font-bold text-center text-gray-800 mt-8 mb-6">Workflow Stages</h2>
      <div className="flex flex-col items-center">
        {vectorBootOrchestrator.stages.map((stage, index) => (
          <React.Fragment key={stage.workflowOpcodeName}>
            <Card className="w-full max-w-4xl mb-6 shadow-md border-t-4 border-blue-400">
              <CardHeader className="flex flex-row items-center space-x-4 pb-2">
                <stage.icon className="h-9 w-9 text-indigo-500" />
                <CardTitle className="text-2xl font-semibold text-gray-900">{stage.title}</CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                <p className="text-base text-gray-700 mb-4">{stage.description}</p>
                <Badge variant="outline" className="mb-3 px-3 py-1 text-sm bg-purple-100 text-purple-800 border-purple-300">
                  Workflow Opcode: {stage.workflowOpcodeName}
                </Badge>
                <Separator className="my-4" />
                <h3 className="text-lg font-medium text-gray-800 mb-3">Atomic Opcodes:</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {stage.atomicOpcodes.map((opcode) => (
                    <div key={opcode.name} className="flex items-start space-x-2">
                      <ArrowRight className="h-4 w-4 text-green-500 flex-shrink-0 mt-1" />
                      <div>
                        <span className="font-semibold text-gray-900">{opcode.name}</span>
                        <p className="text-sm text-gray-600">{opcode.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
            {index < vectorBootOrchestrator.stages.length - 1 && (
              <ArrowDown className="h-8 w-8 text-gray-400 mb-6 animate-bounce" />
            )}
          </React.Fragment>
        ))}
      </div>

      <Card className="mt-10 p-6 bg-yellow-50 border-yellow-200 shadow-sm">
        <CardTitle className="text-xl font-semibold text-yellow-800 flex items-center">
          <Settings className="h-5 w-5 mr-2" />
          Next Steps for Full Simulation
        </CardTitle>
        <CardContent className="mt-4 text-gray-700 space-y-2">
          <p>With atomic and workflow Opcodes defined, the path forward includes:</p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li>Developing concrete semantic definitions and schemas for all fundamental Component Vectors (e.g., CPU_STATE_VECTOR, MEMORY_STATE_VECTOR).</li>
            <li>Implementing the internal logic for each atomic Opcode to transform input vectors into output vectors, reflecting real-world boot actions.</li>
            <li>Creating a robust simulated Vector File System (VFS) to handle read/write operations for boot components and configurations.</li>
            <li>Building dynamic execution environments to run these chained Opcodes, potentially allowing for interactive debugging and visualization of state changes.</li>
            <li>Designing user interfaces for configuration, control, and real-time observability of the entire VectorBoot process.</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
