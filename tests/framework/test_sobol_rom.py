<?xml version="1.0" encoding="UTF-8"?>
<Simulation debug="False">
    <RunInfo>
        <WorkingDir>SobolRom</WorkingDir>
        <Sequence>make,train,test,print</Sequence>
        <batchSize>1</batchSize>
    </RunInfo>

    <Distributions>
        <Uniform name="xd"><low>0</low><high>1</high></Uniform>
        <Uniform name="yd"><low>1</low><high>5</high></Uniform>
        <Uniform name="zd"><low>1</low><high>3</high></Uniform>
    </Distributions>

    <Samplers>
        <Sobol name="sobol">
            <variable name="x1"><distribution>xd</distribution></variable>
            <variable name="x2"><distribution>yd</distribution></variable>
            <variable name="x3"><distribution>zd</distribution></variable>
            <ROM class = 'Models' type = 'ROM'>rom</ROM>
            <TargetEvaluation class = 'Datas' type = 'TimePointSet'>solns</TargetEvaluation>
        </Sobol>
    </Samplers>

    <Models>
        <Dummy name="MyDummy" subType="" print="True"/>
        <ExternalModel name='exp' subType='' ModuleToLoad = './SobolRom/exp'>
            <variable>x1</variable>
            <variable>x2</variable>
            <variable>x3</variable>
            <variable>ans</variable>
        </ExternalModel>
        <ROM name='rom' subType='HDMRRom'>
            <SobolOrder>2</SobolOrder>
            <Target>ans</Target>
            <Features>x1,x2,x3</Features>
            <IndexSet>TotalDegree</IndexSet>
            <PolynomialOrder>3</PolynomialOrder>
            <Interpolation quad='Legendre' poly='Legendre' weight='1'>x1</Interpolation>
            <Interpolation quad='Legendre' poly='Legendre' weight='1'>x2</Interpolation>
            <Interpolation quad='Legendre' poly='Legendre' weight='1'>x3</Interpolation>
        </ROM>
    </Models>

    <Steps>
        <MultiRun name='make'>
            <Sampler class='Samplers'         type='Sobol'        >sobol</Sampler>
            <Input   class='Datas'            type='TimePointSet' >dummyIN</Input>
            <Model   class='Models'           type='ExternalModel'>exp</Model>
            <Output  class='Datas'            type='TimePointSet' >solns</Output>
        </MultiRun>
        <RomTrainer name='train'>
            <Input   class='Datas'            type='TimePointSet' >solns</Input>
            <Output  class='Models'           type='ROM'          >rom</Output>
        </RomTrainer>
        <MultiRun name='test'>
            <Sampler class='Samplers'         type='Sobol'        >sobol</Sampler>
            <Input   class='Datas'            type='TimePointSet' >dummyIN</Input>
            <Model   class='Models'           type='ROM'          >rom</Model>
            <Output  class='Datas'            type='TimePointSet' >tests</Output>
        </MultiRun>
        <OutStreamStep name='print'>
            <Input   class='Datas'            type='TimePointSet' >tests</Input>
            <Output  class='OutStreamManager' type='Print'        >dump</Output>
        </OutStreamStep>
    </Steps>

    <Datas>
        <TimePointSet name="dummyIN">
            <Input>x1,x2,x3</Input>
            <Output>OutputPlaceHolder</Output>
        </TimePointSet>
        <TimePointSet name='tests'>
            <Input>x1,x2,x3</Input>
            <Output>ans</Output>
        </TimePointSet>
        <TimePointSet name='solns'>
            <Input>x1,x2,x3</Input>
            <Output>ans</Output>
        </TimePointSet>
    </Datas>

    <OutStreamManager>
        <Print name='dump'>
            <type>csv</type>
            <source>tests</source>
        </Print>
    </OutStreamManager>
</Simulation>
