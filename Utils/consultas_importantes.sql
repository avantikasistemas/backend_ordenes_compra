--CONSULTA DE BUSQUEDA DE CLIENTE
select * from terceros where nit = 890101977;  -- Buscar toda la informacion por el Tercero
 
SELECT t.nit, t.nombres, tv.coordinador, tv.ejecutivo, dbo.terceros_16.descripcion AS 'Tipo de cliente', dbo.terceros_2.descripcion AS 'Zona'
FROM   dbo.terceros AS t 
INNER JOIN dbo.terceros_ventas AS tv ON t.concepto_2 = tv.concepto_2 
INNER JOIN dbo.terceros_16 ON t.concepto_16 = dbo.terceros_16.concepto_16 
INNER JOIN dbo.terceros_2 ON t.concepto_2 = dbo.terceros_2.concepto_2
WHERE t.nit = 890101977; -- Busca informacion relevante para Cotizaciones.
 
-- BUSCAR COTIZACION.
select * from documentos_ped where numero = 168474 and sw = 2; -- Informacion General de la cotizacion
select * from documentos_lin_ped where numero = 168474 and sw = 2; -- Informacion detallada de los items o productos cotizados
 
-- TIPOS DE CLIENTES
select * from terceros_16 -- Tipos de clientes.
 
-- ESTADO DE UNA COTIZACION
select * from tipo_transacciones_concep2_ped where sw = 2 order by concepto asc;
 
-- CONCEPTO DE UNA COTIZACION
select * from tipo_transacciones_concep_ped where sw = 2;

-- CONDICIONES DE PAGO DE UNA CONDICIÓN
select * from condiciones_pago;
 
--HISTORIAL DE COMPRA DE UN CLIENTE
select * from documentos_lin where tipo = 'FC' and nit = 8901065274; -- Historial de Factura de un cliente, se muestra el codigo de la referencia comprada
-- Otros nit para hacer la prueba (8901016922) (9005844242)


-- Aplicar cambios de nit a FC and RM
-- Esto se usa cuando requieren realizar el cambio de nit porque se equivocaron
select * from documentos where tipo = 'FC' and numero = 71777;
update documentos set nit = 8001359133 where tipo = 'FC' and numero = 71777;
 
select * from documentos_lin where tipo = 'FC' and numero = 71777;
update documentos_lin set nit = 8001359133 where tipo = 'FC' and numero = 71777;
 
select * from movimiento where tipo = 'FC' and numero = 71777;
update movimiento set nit = 8001359133 where tipo = 'FC' and numero = 71777;


------------------------------------------------------------------------------------------------------------------------------------------------------------
-- querys 26 febrero 2025
ALTER TABLE seguimiento_coti
ADD motivo_no_cotizacion VARCHAR(255) NULL, desvio_oportunidad VARCHAR(255) NULL;

ALTER TABLE seguimiento_coti
ADD item_revisado_cumple SMALLINT DEFAULT(0) NULL, item_revisado_muestra SMALLINT DEFAULT(0) NULL, porcentaje_muestra SMALLINT DEFAULT(0), desvio_calidad VARCHAR(255) NULL;

------------------------------------------------------------------------------------------------------------------------------------------------------------
