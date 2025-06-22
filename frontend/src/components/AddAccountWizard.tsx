import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
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
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  CheckCircle,
  XCircle,
  Loader2,
  Shield,
  Key,
  Clock,
  Copy,
  Download,
} from 'lucide-react';
import { toast } from 'react-hot-toast';

// Schemas de validação para cada método de auth
const baseAccountSchema = z.object({
  name: z.string().min(1, 'Nome é obrigatório'),
  accountId: z.string().regex(/^\d{12}$/, 'Account ID deve ter 12 dígitos'),
  region: z.string().min(1, 'Região é obrigatória'),
  contactEmail: z.string().email('Email inválido').optional(),
  slaTier: z.enum(['basic', 'standard', 'premium']),
});

const crossAccountRoleSchema = baseAccountSchema.extend({
  authMethod: z.literal('cross_account_role'),
  roleArn: z.string().regex(/^arn:aws:iam::\d{12}:role\/.*/, 'ARN da role inválido'),
  externalId: z.string().min(1, 'External ID é obrigatório'),
  sessionName: z.string().optional(),
});

const iamKeysSchema = baseAccountSchema.extend({
  authMethod: z.literal('iam_keys'),
  accessKeyId: z.string().regex(/^AKIA[0-9A-Z]{16}$/, 'Access Key ID inválido'),
  secretAccessKey: z.string().min(1, 'Secret Access Key é obrigatório'),
  sessionToken: z.string().optional(),
});

const tempCredentialsSchema = baseAccountSchema.extend({
  authMethod: z.literal('temp_credentials'),
  stsToken: z.string().min(1, 'STS Token é obrigatório'),
  duration: z.number().min(900).max(43200), // 15min a 12h
  mfaToken: z.string().optional(),
});

type AuthMethod = 'cross_account_role' | 'iam_keys' | 'temp_credentials';
type AccountFormData = z.infer<typeof crossAccountRoleSchema> | 
                     z.infer<typeof iamKeysSchema> | 
                     z.infer<typeof tempCredentialsSchema>;

interface AddAccountWizardProps {
  onClose: () => void;
  onAccountAdded: (account: any) => void;
}

interface TestResult {
  success: boolean;
  message: string;
  permissions?: string[];
  discoveredServices?: any[];
}

export function AddAccountWizard({ onClose, onAccountAdded }: AddAccountWizardProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [authMethod, setAuthMethod] = useState<AuthMethod>('cross_account_role');
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const getSchemaForAuthMethod = (method: AuthMethod) => {
    switch (method) {
      case 'cross_account_role':
        return crossAccountRoleSchema;
      case 'iam_keys':
        return iamKeysSchema;
      case 'temp_credentials':
        return tempCredentialsSchema;
    }
  };

  const form = useForm<AccountFormData>({
    resolver: zodResolver(getSchemaForAuthMethod(authMethod)),
    defaultValues: {
      authMethod,
      name: '',
      accountId: '',
      region: 'us-east-1',
      slaTier: 'standard',
    },
  });

  const testConnection = async (data: AccountFormData) => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/accounts/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      
      const result = await response.json();
      setTestResult(result);
      
      if (result.success) {
        toast.success('Conexão testada com sucesso!');
      } else {
        toast.error(`Erro na conexão: ${result.message}`);
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Erro ao testar conexão',
      });
      toast.error('Erro ao testar conexão');
    } finally {
      setIsLoading(false);
    }
  };

  const onSubmit = async (data: AccountFormData) => {
    if (currentStep === 2 && !testResult?.success) {
      toast.error('Teste a conexão antes de continuar');
      return;
    }

    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
      return;
    }

    // Salvar conta
    setIsLoading(true);
    try {
      const response = await fetch('/api/accounts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      
      if (response.ok) {
        const account = await response.json();
        toast.success('Conta adicionada com sucesso!');
        onAccountAdded(account);
        onClose();
      } else {
        toast.error('Erro ao adicionar conta');
      }
    } catch (error) {
      toast.error('Erro ao adicionar conta');
    } finally {
      setIsLoading(false);
    }
  };

  const generateCloudFormationTemplate = () => {
    const template = {
      AWSTemplateFormatVersion: '2010-09-09',
      Description: 'SelectNOC IA - Cross-Account Role Setup',
      Parameters: {
        SelectNOCAccountId: {
          Type: 'String',
          Default: 'YOUR_ACCOUNT_ID',
          Description: 'Account ID da SelectNOC IA',
        },
        ExternalId: {
          Type: 'String',
          Default: `selectnoc-${Date.now()}`,
          Description: 'External ID único para segurança',
        },
      },
      Resources: {
        SelectNOCRole: {
          Type: 'AWS::IAM::Role',
          Properties: {
            RoleName: 'SelectNOC-ReadOnlyRole',
            AssumeRolePolicyDocument: {
              Version: '2012-10-17',
              Statement: [
                {
                  Effect: 'Allow',
                  Principal: {
                    AWS: '${SelectNOCAccountId}',
                  },
                  Action: 'sts:AssumeRole',
                  Condition: {
                    StringEquals: {
                      'sts:ExternalId': '${ExternalId}',
                    },
                  },
                },
              ],
            },
            ManagedPolicyArns: [
              'arn:aws:iam::aws:policy/ReadOnlyAccess',
            ],
            Policies: [
              {
                PolicyName: 'SelectNOC-CloudWatchLogs',
                PolicyDocument: {
                  Version: '2012-10-17',
                  Statement: [
                    {
                      Effect: 'Allow',
                      Action: [
                        'logs:DescribeLogGroups',
                        'logs:DescribeLogStreams',
                        'logs:GetLogEvents',
                        'logs:StartQuery',
                        'logs:GetQueryResults',
                        'logs:FilterLogEvents',
                      ],
                      Resource: '*',
                    },
                  ],
                },
              },
            ],
          },
        },
      },
      Outputs: {
        RoleArn: {
          Description: 'ARN da role criada',
          Value: { 'Fn::GetAtt': ['SelectNOCRole', 'Arn'] },
        },
        ExternalId: {
          Description: 'External ID para usar na SelectNOC IA',
          Value: '${ExternalId}',
        },
      },
    };

    return JSON.stringify(template, null, 2);
  };

  const downloadTemplate = () => {
    const template = generateCloudFormationTemplate();
    const blob = new Blob([template], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'selectnoc-setup.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const copyTemplate = () => {
    const template = generateCloudFormationTemplate();
    navigator.clipboard.writeText(template);
    toast.success('Template copiado para o clipboard!');
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-4xl max-h-[90vh] overflow-y-auto m-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Adicionar Conta AWS - Passo {currentStep} de 3
          </CardTitle>
          <CardDescription>
            Configure o acesso a uma nova conta AWS para monitoramento
          </CardDescription>
        </CardHeader>

        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              {/* Passo 1: Informações Básicas */}
              {currentStep === 1 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Informações da Conta</h3>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Nome do Cliente</FormLabel>
                          <FormControl>
                            <Input placeholder="ex: ACME Corp" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="accountId"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>AWS Account ID</FormLabel>
                          <FormControl>
                            <Input placeholder="123456789012" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="region"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Região Principal</FormLabel>
                          <FormControl>
                            <select className="w-full p-2 border rounded" {...field}>
                              <option value="us-east-1">US East (N. Virginia)</option>
                              <option value="us-west-2">US West (Oregon)</option>
                              <option value="eu-west-1">Europe (Ireland)</option>
                              <option value="sa-east-1">South America (São Paulo)</option>
                            </select>
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="slaTier"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>SLA Tier</FormLabel>
                          <FormControl>
                            <select className="w-full p-2 border rounded" {...field}>
                              <option value="basic">Basic (24h response)</option>
                              <option value="standard">Standard (4h response)</option>
                              <option value="premium">Premium (1h response)</option>
                            </select>
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <FormField
                    control={form.control}
                    name="contactEmail"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Email de Contato (Opcional)</FormLabel>
                        <FormControl>
                          <Input placeholder="admin@cliente.com" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              )}

              {/* Passo 2: Método de Autenticação */}
              {currentStep === 2 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Método de Autenticação</h3>
                  
                  <Tabs value={authMethod} onValueChange={(value) => setAuthMethod(value as AuthMethod)}>
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="cross_account_role" className="flex items-center gap-2">
                        <Shield className="h-4 w-4" />
                        Cross-Account Role
                        <Badge variant="outline" className="ml-1">Recomendado</Badge>
                      </TabsTrigger>
                      <TabsTrigger value="iam_keys" className="flex items-center gap-2">
                        <Key className="h-4 w-4" />
                        IAM Keys
                      </TabsTrigger>
                      <TabsTrigger value="temp_credentials" className="flex items-center gap-2">
                        <Clock className="h-4 w-4" />
                        Temporárias
                      </TabsTrigger>
                    </TabsList>

                    <TabsContent value="cross_account_role" className="space-y-4">
                      <Alert>
                        <Shield className="h-4 w-4" />
                        <AlertDescription>
                          Método mais seguro. O cliente executa um CloudFormation template para criar a role.
                        </AlertDescription>
                      </Alert>

                      <div className="flex gap-2">
                        <Button type="button" variant="outline" onClick={downloadTemplate}>
                          <Download className="h-4 w-4 mr-2" />
                          Download Template
                        </Button>
                        <Button type="button" variant="outline" onClick={copyTemplate}>
                          <Copy className="h-4 w-4 mr-2" />
                          Copiar Template
                        </Button>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <FormField
                          control={form.control}
                          name="roleArn"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Role ARN</FormLabel>
                              <FormControl>
                                <Input 
                                  placeholder="arn:aws:iam::123456789012:role/SelectNOC-ReadOnlyRole" 
                                  {...field} 
                                />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />

                        <FormField
                          control={form.control}
                          name="externalId"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>External ID</FormLabel>
                              <FormControl>
                                <Input placeholder="selectnoc-unique-id" {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </div>
                    </TabsContent>

                    <TabsContent value="iam_keys" className="space-y-4">
                      <Alert>
                        <Key className="h-4 w-4" />
                        <AlertDescription>
                          Cliente cria usuário IAM com permissões read-only e compartilha as keys.
                        </AlertDescription>
                      </Alert>

                      <div className="grid grid-cols-2 gap-4">
                        <FormField
                          control={form.control}
                          name="accessKeyId"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Access Key ID</FormLabel>
                              <FormControl>
                                <Input placeholder="AKIAIOSFODNN7EXAMPLE" {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />

                        <FormField
                          control={form.control}
                          name="secretAccessKey"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Secret Access Key</FormLabel>
                              <FormControl>
                                <Input 
                                  type="password" 
                                  placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" 
                                  {...field} 
                                />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </div>

                      <FormField
                        control={form.control}
                        name="sessionToken"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Session Token (Opcional)</FormLabel>
                            <FormControl>
                              <Input 
                                type="password" 
                                placeholder="Para credenciais temporárias" 
                                {...field} 
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </TabsContent>

                    <TabsContent value="temp_credentials" className="space-y-4">
                      <Alert>
                        <Clock className="h-4 w-4" />
                        <AlertDescription>
                          Credenciais temporárias via STS. Útil para testes ou acesso temporário.
                        </AlertDescription>
                      </Alert>

                      <div className="grid grid-cols-2 gap-4">
                        <FormField
                          control={form.control}
                          name="stsToken"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>STS Token</FormLabel>
                              <FormControl>
                                <Input 
                                  type="password" 
                                  placeholder="Token temporário do STS" 
                                  {...field} 
                                />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />

                        <FormField
                          control={form.control}
                          name="duration"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Duração (segundos)</FormLabel>
                              <FormControl>
                                <Input 
                                  type="number" 
                                  placeholder="3600" 
                                  min="900" 
                                  max="43200" 
                                  {...field} 
                                />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </div>
                    </TabsContent>
                  </Tabs>

                  {/* Teste de Conexão */}
                  <div className="space-y-4">
                    <Button 
                      type="button" 
                      onClick={() => testConnection(form.getValues())} 
                      disabled={isLoading}
                      className="w-full"
                    >
                      {isLoading ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : null}
                      Testar Conexão
                    </Button>

                    {testResult && (
                      <Alert className={testResult.success ? 'border-green-500' : 'border-red-500'}>
                        {testResult.success ? (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-500" />
                        )}
                        <AlertDescription>
                          {testResult.message}
                          {testResult.permissions && (
                            <div className="mt-2">
                              <p className="text-sm font-semibold">Permissões detectadas:</p>
                              <ul className="text-sm list-disc list-inside">
                                {testResult.permissions.map((perm, idx) => (
                                  <li key={idx}>{perm}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                </div>
              )}

              {/* Passo 3: Confirmação */}
              {currentStep === 3 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Confirmação</h3>
                  
                  <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                    <p><strong>Cliente:</strong> {form.watch('name')}</p>
                    <p><strong>Account ID:</strong> {form.watch('accountId')}</p>
                    <p><strong>Região:</strong> {form.watch('region')}</p>
                    <p><strong>Método de Auth:</strong> {authMethod}</p>
                    <p><strong>SLA Tier:</strong> {form.watch('slaTier')}</p>
                  </div>

                  {testResult?.discoveredServices && (
                    <div>
                      <p className="font-semibold">Serviços Descobertos:</p>
                      <div className="grid grid-cols-3 gap-2 mt-2">
                        {testResult.discoveredServices.map((service, idx) => (
                          <Badge key={idx} variant="outline">
                            {service.type}: {service.count}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Botões de Navegação */}
              <div className="flex justify-between">
                <div>
                  {currentStep > 1 && (
                    <Button 
                      type="button" 
                      variant="outline" 
                      onClick={() => setCurrentStep(currentStep - 1)}
                    >
                      Anterior
                    </Button>
                  )}
                </div>
                
                <div className="flex gap-2">
                  <Button type="button" variant="outline" onClick={onClose}>
                    Cancelar
                  </Button>
                  
                  <Button type="submit" disabled={isLoading}>
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : null}
                    {currentStep === 3 ? 'Adicionar Conta' : 'Próximo'}
                  </Button>
                </div>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}

