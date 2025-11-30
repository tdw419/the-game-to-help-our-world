import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/components/ui/use-toast';

import { LlmProvider } from '@/types/llm-config';
import { llmConfigMockApiClient } from '@/services/LlmConfigMockApiClient';
import { Loader2 } from 'lucide-react';

// Re-use the formSchema from AddLlmProviderDialog for consistency
const formSchema = z.object({
  name: z.string().min(2, {
    message: 'Name must be at least 2 characters.',
  }).max(50, {
    message: 'Name must not be longer than 50 characters.',
  }),
  type: z.enum(['OpenAI', 'Google', 'Azure', 'HuggingFace', 'Custom'], {
    required_error: 'You need to select a provider type.',
  }),
  apiKey: z.string().min(10, {
    message: 'API Key must be at least 10 characters.',
  }),
  baseUrl: z.string().url({
    message: 'Base URL must be a valid URL.',
  }).max(100, {
    message: 'Base URL must not be longer than 100 characters.',
  }),
  isActive: z.boolean().default(true),
});

interface EditLlmProviderDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  initialData: LlmProvider;
  onProviderUpdated: () => void;
}

export default function EditLlmProviderDialog({
  isOpen,
  onOpenChange,
  initialData,
  onProviderUpdated,
}: EditLlmProviderDialogProps) {
  const { toast } = useToast();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    // Set initial values from initialData when the component mounts or initialData changes
    defaultValues: initialData,
  });

  // Reset form with initialData whenever the dialog opens or initialData changes
  useEffect(() => {
    if (isOpen && initialData) {
      form.reset(initialData);
    }
  }, [isOpen, initialData, form]);


  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    try {
      const updatedProvider = await llmConfigMockApiClient.updateLlmProvider(initialData.id, {
        ...values,
        id: initialData.id, // Ensure ID is explicitly passed and not accidentally changed
        createdAt: initialData.createdAt, // Preserve original creation timestamp
      });
      if (updatedProvider) {
        toast({
          title: 'Success!',
          description: `LLM Provider "${updatedProvider.name}" updated.`,
          variant: 'default',
        });
        onOpenChange(false); // Close dialog
        onProviderUpdated(); // Notify parent to refresh list
      } else {
        toast({
          title: 'Error',
          description: 'Failed to update LLM provider: Provider not found.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Failed to update LLM provider:', error);
      toast({
        title: 'Error',
        description: 'Failed to update LLM provider. Please try again.',
        variant: 'destructive',
      });
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit LLM Provider</DialogTitle>
          <DialogDescription>
            Modify the configuration for "{initialData.name}".
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Provider Name</FormLabel>
                  <FormControl>
                    <Input placeholder="OpenAI (Primary)" {...field} />
                  </FormControl>
                  <FormDescription>
                    A friendly name for this LLM provider.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Provider Type</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a provider type" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="OpenAI">OpenAI</SelectItem>
                      <SelectItem value="Google">Google</SelectItem>
                      <SelectItem value="Azure">Azure</SelectItem>
                      <SelectItem value="HuggingFace">HuggingFace</SelectItem>
                      <SelectItem value="Custom">Custom</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    The technology or platform for this LLM provider.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="apiKey"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>API Key</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="sk-..." {...field} />
                  </FormControl>
                  <FormDescription>
                    The API key for authentication with the provider.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="baseUrl"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Base URL</FormLabel>
                  <FormControl>
                    <Input placeholder="https://api.openai.com/v1" {...field} />
                  </FormControl>
                  <FormDescription>
                    The base URL for the provider's API endpoint.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="isActive"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">Active</FormLabel>
                    <FormDescription>
                      Enable or disable this provider.
                    </FormDescription>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                'Save Changes'
              )}
            </Button>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
